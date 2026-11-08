from collections import defaultdict

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent.assistant import chat
from agent.tools.arrival import buscar_parada_proxima_com_previsao
from agent.tools.favoritos import (
    listar_linhas_favoritas,
    remover_linha_favorita,
    salvar_linha_favorita,
)
from agent.tools.geocoding import geocodificar_endereco
from pipeline.api.sptrans_client import buscar_linhas

_state: dict[int, dict] = {}
_history: dict[int, list] = defaultdict(list)

_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🚌 Meu ônibus", callback_data="meu_onibus")],
    [InlineKeyboardButton("⭐ Favoritos", callback_data="menu_favoritos")],
])

_MENU_FAVORITOS = InlineKeyboardMarkup([
    [InlineKeyboardButton("💾 Salvar linha", callback_data="fav_salvar")],
    [InlineKeyboardButton("📋 Listar favoritos", callback_data="fav_listar")],
    [InlineKeyboardButton("🗑️ Remover linha", callback_data="fav_remover")],
    [InlineKeyboardButton("◀️ Voltar", callback_data="menu_principal")],
])

_LOC_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📍 Compartilhar localização", request_location=True)]],
    one_time_keyboard=True,
    resize_keyboard=True,
)


def _inline_voltar(callback="menu_principal"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Voltar", callback_data=callback)]])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _state.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "Olá! Sou o *SPTrans Assistant*.\n"
        "Te ajudo a saber quando seu ônibus está chegando.",
        parse_mode="Markdown",
        reply_markup=_MENU,
    )


# ── Mensagens de texto ────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    step = _state.get(chat_id, {}).get("step")
    text = update.message.text

    if step == "salvar_aguarda_numero":
        await _salvar_linha(update, chat_id, text)
        return

    if step == "remover_aguarda_numero":
        await _remover_linha(update, chat_id, text)
        return

    if step == "get_location":
        await _fetch_arrival_text(update, chat_id, text)
        return

    # Chat livre — só para busca por destino/RAG
    _history[chat_id].append({"role": "user", "content": text})
    await update.message.chat.send_action("typing")
    response = chat(_history[chat_id])
    _history[chat_id].append({"role": "assistant", "content": response})
    await update.message.reply_text(response)


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if _state.get(chat_id, {}).get("step") == "get_location":
        loc = update.message.location
        await _fetch_arrival_coords(update, chat_id, loc.latitude, loc.longitude)


# ── Callbacks ─────────────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data

    # Menus
    if data == "menu_principal":
        _state.pop(chat_id, None)
        await query.edit_message_text("Menu principal:", reply_markup=_MENU)
    elif data == "menu_favoritos":
        await query.edit_message_text("Favoritos:", reply_markup=_MENU_FAVORITOS)

    # Favoritos
    elif data == "fav_listar":
        await _cb_listar(query)
    elif data == "fav_salvar":
        _state[chat_id] = {"step": "salvar_aguarda_numero"}
        await query.edit_message_text(
            "Digite o número da linha que deseja salvar:\n_(ex: 5119-10, 695T-10)_",
            parse_mode="Markdown",
            reply_markup=_inline_voltar("menu_favoritos"),
        )
    elif data == "fav_remover":
        _state[chat_id] = {"step": "remover_aguarda_numero"}
        await query.edit_message_text(
            "Digite o número da linha que deseja remover:",
            reply_markup=_inline_voltar("menu_favoritos"),
        )

    # Fluxo meu ônibus
    elif data in ("meu_onibus", "meu_onibus_again"):
        await _start_flow(query, chat_id)
    elif data.startswith("line:"):
        await _select_line(query, chat_id, data.split(":", 1)[1])
    elif data.startswith("dir:"):
        await _select_direction(query, chat_id, int(data.split(":")[1]))

    # Localização
    elif data == "loc_gps":
        await query.edit_message_text(
            "Ok! Clique no botão abaixo para compartilhar sua localização 👇",
            reply_markup=None,
        )
        await query.message.reply_text(
            "📍 Compartilhe sua localização:",
            reply_markup=_LOC_KEYBOARD,
        )
    elif data == "loc_texto":
        _state[chat_id]["step"] = "get_location"
        await query.edit_message_text("Digite seu endereço ou ponto de referência:")

    elif data == "cancel":
        _state.pop(chat_id, None)
        await query.edit_message_text("Cancelado.", reply_markup=_MENU)


# ── Favoritos ─────────────────────────────────────────────────────────────────

async def _cb_listar(query):
    result = listar_linhas_favoritas()
    favoritos = result.get("favoritos", [])
    if not favoritos:
        await query.edit_message_text(
            "Nenhum favorito salvo ainda.",
            reply_markup=_inline_voltar("menu_favoritos"),
        )
        return
    linhas = "\n".join(f"• {f['numero_linha']} → {f['destino']}" for f in favoritos)
    await query.edit_message_text(
        f"*Seus favoritos:*\n{linhas}",
        parse_mode="Markdown",
        reply_markup=_inline_voltar("menu_favoritos"),
    )


async def _salvar_linha(update: Update, chat_id: int, numero: str):
    _state.pop(chat_id, None)
    await update.message.chat.send_action("typing")

    linhas = buscar_linhas(numero.strip())
    if not linhas:
        await update.message.reply_text(
            f"Linha *{numero}* não encontrada na API.",
            parse_mode="Markdown",
            reply_markup=_MENU_FAVORITOS,
        )
        return

    salvos = []
    for l in linhas:
        salvar_linha_favorita(l["letreiro"], l["codigo_linha"], l["destino"])
        salvos.append(f"• sentido {l['destino']}")

    confirmacao = "\n".join(salvos)
    await update.message.reply_text(
        f"✅ *Linha {linhas[0]['letreiro']} salva!*\n{confirmacao}",
        parse_mode="Markdown",
        reply_markup=_MENU_FAVORITOS,
    )


async def _remover_linha(update: Update, chat_id: int, numero: str):
    _state.pop(chat_id, None)
    result = remover_linha_favorita(numero.strip())
    await update.message.reply_text(
        result.get("mensagem", "Feito."),
        reply_markup=_MENU_FAVORITOS,
    )


# ── Fluxo meu ônibus ──────────────────────────────────────────────────────────

async def _start_flow(query, chat_id: int):
    result = listar_linhas_favoritas()
    favoritos = result.get("favoritos", [])
    if not favoritos:
        await query.edit_message_text(
            "Nenhum favorito salvo.\nUse *⭐ Favoritos → 💾 Salvar linha* para adicionar.",
            parse_mode="Markdown",
            reply_markup=_MENU,
        )
        return

    by_line: dict[str, list] = defaultdict(list)
    for f in favoritos:
        by_line[f["numero_linha"]].append(f)

    _state[chat_id] = {"step": "select_line", "by_line": dict(by_line)}

    keyboard = [
        [InlineKeyboardButton(f"Linha {num}", callback_data=f"line:{num}")]
        for num in by_line
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])

    await query.edit_message_text(
        "Qual linha você precisa agora?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _select_line(query, chat_id: int, numero_linha: str):
    directions = _state[chat_id]["by_line"][numero_linha]

    if len(directions) == 1:
        _state[chat_id] = {"step": "ask_location", "selected": directions[0]}
    else:
        _state[chat_id]["step"] = "select_direction"
        _state[chat_id]["directions"] = directions
        keyboard = [
            [InlineKeyboardButton(d["destino"], callback_data=f"dir:{i}")]
            for i, d in enumerate(directions)
        ]
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
        await query.edit_message_text("Qual destino?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await _ask_location(query, chat_id)


async def _select_direction(query, chat_id: int, index: int):
    selected = _state[chat_id]["directions"][index]
    _state[chat_id] = {"step": "ask_location", "selected": selected}
    await _ask_location(query, chat_id)


async def _ask_location(query, chat_id: int):
    selected = _state[chat_id]["selected"]
    _state[chat_id]["step"] = "get_location"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📍 Usar minha localização", callback_data="loc_gps")],
        [InlineKeyboardButton("✍️ Digitar endereço", callback_data="loc_texto")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
    ])
    await query.edit_message_text(
        f"*Linha {selected['numero_linha']} → {selected['destino']}*\n\n"
        "Como prefere informar sua localização?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


# ── Busca de previsão ─────────────────────────────────────────────────────────

async def _fetch_arrival_text(update: Update, chat_id: int, location_text: str):
    state = _state.get(chat_id, {})
    selected = state.get("selected")
    if not selected:
        await update.message.reply_text("Sessão expirada. Use o menu para começar.", reply_markup=_MENU)
        _state.pop(chat_id, None)
        return
    _state.pop(chat_id, None)
    await update.message.chat.send_action("typing")
    try:
        loc = geocodificar_endereco(location_text)
    except Exception:
        await update.message.reply_text("Erro ao buscar o endereço. Tente novamente.", reply_markup=_MENU)
        return
    if "erro" in loc:
        await update.message.reply_text(
            "Não encontrei esse endereço. Tente de outra forma.",
        )
        _state[chat_id] = {"step": "get_location", "selected": selected}
        return
    await _send_arrival(update, selected, loc["latitude"], loc["longitude"])


async def _fetch_arrival_coords(update: Update, chat_id: int, lat: float, lon: float):
    state = _state.get(chat_id, {})
    selected = state.get("selected")
    if not selected:
        await update.message.reply_text("Sessão expirada. Use o menu para começar.", reply_markup=_MENU)
        _state.pop(chat_id, None)
        return
    _state.pop(chat_id, None)
    await update.message.chat.send_action("typing")
    await _send_arrival(update, selected, lat, lon)


async def _send_arrival(update: Update, selected: dict, lat: float, lon: float):
    keyboard = [
        [InlineKeyboardButton("🔄 Consultar novamente", callback_data="meu_onibus_again")],
        [InlineKeyboardButton("◀️ Menu", callback_data="menu_principal")],
    ]
    try:
        result = buscar_parada_proxima_com_previsao(selected["codigo_linha"], lat, lon)
    except Exception:
        await update.message.reply_text(
            "Erro ao consultar a API SPTrans. Tente em alguns instantes.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if "erro" in result:
        await update.message.reply_text(
            f"Sem previsão para {selected['numero_linha']} → {selected['destino']} agora.\nTente em alguns minutos.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    acessivel = " ♿" if result.get("acessivel") else ""
    nome_parada = result.get("parada") or "Parada próxima"
    maps_url = (
        f"https://www.google.com/maps/dir/{lat},{lon}/"
        f"{result['parada_lat']},{result['parada_lon']}"
    )
    msg = (
        f"🚌 *Linha {selected['numero_linha']} → {selected['destino']}*\n\n"
        f"📍 {nome_parada}\n"
        f"📏 {result['distancia_metros_ate_parada']}m de você\n"
        f"🕐 Chegada: *{result['previsao_chegada']}*\n"
        f"🔢 Veículo {result['prefixo_veiculo']}{acessivel}"
    )
    keyboard.insert(0, [InlineKeyboardButton("🗺️ Ver no mapa", url=maps_url)])
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
