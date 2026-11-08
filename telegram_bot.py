from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from agent.tools.favoritos import listar_linhas_favoritas
from agent.tools.geocoding import geocodificar_endereco

# Per-user guided flow state
_state: dict[int, dict] = {}
# Per-user chat history for AI conversations
_history: dict[int, list] = defaultdict(list)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚌 Meu ônibus", callback_data="meu_onibus")]]
    await update.message.reply_text(
        "Olá! Sou o SPTrans Assistant.\n"
        "Te ajudo a saber quando seu ônibus está chegando.\n\n"
        "Use o botão abaixo ou me pergunte qualquer coisa sobre linhas.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if _state.get(chat_id, {}).get("step") == "get_location":
        await _fetch_arrival(update, chat_id, text)
        return

    _history[chat_id].append({"role": "user", "content": text})
    await update.message.chat.send_action("typing")
    response = chat(_history[chat_id])
    _history[chat_id].append({"role": "assistant", "content": response})
    await update.message.reply_text(response)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data

    if data == "meu_onibus":
        await _start_flow(query, chat_id)
    elif data == "meu_onibus_again":
        await _start_flow(query, chat_id)
    elif data.startswith("line:"):
        await _select_line(query, chat_id, data.split(":", 1)[1])
    elif data.startswith("dir:"):
        await _select_direction(query, chat_id, int(data.split(":")[1]))
    elif data == "cancel":
        _state.pop(chat_id, None)
        await query.edit_message_text("Cancelado.")


async def _start_flow(query, chat_id: int):
    result = listar_linhas_favoritas()
    favoritos = result.get("favoritos", [])
    if not favoritos:
        await query.edit_message_text(
            "Você não tem favoritos salvos ainda.\n"
            "Diga o número de uma linha e eu busco a previsão."
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
    by_line = _state[chat_id]["by_line"]
    directions = by_line[numero_linha]

    if len(directions) == 1:
        _state[chat_id] = {"step": "get_location", "selected": directions[0]}
        await query.edit_message_text(
            f"Linha {numero_linha} → {directions[0]['destino']}\n\n"
            "Qual sua localização atual? (rua, bairro ou ponto de referência)"
        )
    else:
        _state[chat_id]["step"] = "select_direction"
        _state[chat_id]["directions"] = directions

        # Use index in callback_data to stay under 64-byte limit
        keyboard = [
            [InlineKeyboardButton(d["destino"], callback_data=f"dir:{i}")]
            for i, d in enumerate(directions)
        ]
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])

        await query.edit_message_text(
            "Qual destino?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def _select_direction(query, chat_id: int, index: int):
    directions = _state[chat_id]["directions"]
    selected = directions[index]
    _state[chat_id] = {"step": "get_location", "selected": selected}
    await query.edit_message_text(
        f"Sentido {selected['destino']}\n\n"
        "Qual sua localização atual? (rua, bairro ou ponto de referência)"
    )


async def _fetch_arrival(update: Update, chat_id: int, location_text: str):
    selected = _state.pop(chat_id)["selected"]
    await update.message.chat.send_action("typing")

    loc = geocodificar_endereco(location_text)
    if "erro" in loc:
        await update.message.reply_text(
            "Não encontrei essa localização. Tente informar de outra forma."
        )
        _state[chat_id] = {"step": "get_location", "selected": selected}
        return

    result = buscar_parada_proxima_com_previsao(
        selected["codigo_linha"], loc["latitude"], loc["longitude"]
    )

    if "erro" in result:
        msg = (
            f"Sem previsão para {selected['numero_linha']} → {selected['destino']} agora.\n"
            "Tente em alguns minutos."
        )
    else:
        acessivel = " ♿" if result.get("acessivel") else ""
        msg = (
            f"🚌 Linha {selected['numero_linha']} → {selected['destino']}\n\n"
            f"📍 {result['parada']}\n"
            f"📏 {result['distancia_metros_ate_parada']}m de você\n"
            f"🕐 Chegada: {result['previsao_chegada']}\n"
            f"🔢 Veículo {result['prefixo_veiculo']}{acessivel}"
        )

    keyboard = [[InlineKeyboardButton("🚌 Consultar novamente", callback_data="meu_onibus_again")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
