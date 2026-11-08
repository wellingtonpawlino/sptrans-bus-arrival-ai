from collections import defaultdict

import streamlit as st

from agent.assistant import chat
from agent.tools.arrival import buscar_parada_proxima_com_previsao
from agent.tools.favoritos import listar_linhas_favoritas
from agent.tools.geocoding import geocodificar_endereco

st.set_page_config(page_title="SPTrans Assistant", page_icon="🚌")
st.title("SPTrans Assistant")
st.caption("Assistente de mobilidade urbana de São Paulo")

_DEFAULTS = {
    "messages": [],
    "step": None,   # None | "select_line" | "select_direction" | "get_location"
    "gdata": {},    # dados do fluxo guiado
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _add(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def _start_flow():
    result = listar_linhas_favoritas()
    favoritos = result.get("favoritos", [])
    if not favoritos:
        _add("assistant", "Você não tem favoritos salvos ainda. Diga o número de uma linha e eu busco a previsão.")
        return

    by_line = defaultdict(list)
    for f in favoritos:
        by_line[f["numero_linha"]].append(f)

    st.session_state.step = "select_line"
    st.session_state.gdata = {"by_line": dict(by_line)}
    lines = ", ".join(by_line.keys())
    _add("assistant", f"Qual dessas linhas você precisa agora?\n{lines}")


def _select_line(numero_linha: str):
    by_line = st.session_state.gdata["by_line"]
    directions = by_line[numero_linha]
    _add("user", f"Linha {numero_linha}")

    if len(directions) == 1:
        st.session_state.gdata["selected"] = directions[0]
        st.session_state.step = "get_location"
        _add("assistant", f"Sentido **{directions[0]['destino']}**.\nQual sua localização atual?")
    else:
        st.session_state.gdata["directions"] = directions
        st.session_state.step = "select_direction"
        opts = " · ".join(d["destino"] for d in directions)
        _add("assistant", f"Qual destino?\n{opts}")


def _select_direction(direction: dict):
    _add("user", direction["destino"])
    st.session_state.gdata["selected"] = direction
    st.session_state.step = "get_location"
    _add("assistant", "Qual sua localização atual? (rua, bairro ou ponto de referência)")


def _fetch_arrival(location_text: str):
    selected = st.session_state.gdata["selected"]
    _add("user", location_text)

    loc = geocodificar_endereco(location_text)
    if "erro" in loc:
        _add("assistant", "Não encontrei essa localização. Tente informar de outra forma.")
        return

    result = buscar_parada_proxima_com_previsao(
        selected["codigo_linha"], loc["latitude"], loc["longitude"]
    )

    st.session_state.step = None
    st.session_state.gdata = {}

    if "erro" in result:
        msg = f"Sem previsão para linha {selected['numero_linha']} sentido {selected['destino']} agora. Tente em alguns minutos."
    else:
        acessivel = " ♿" if result.get("acessivel") else ""
        msg = (
            f"**Linha {selected['numero_linha']} → {selected['destino']}**\n\n"
            f"📍 {result['parada']} — {result['distancia_metros_ate_parada']}m de você\n"
            f"🕐 Chegada: **{result['previsao_chegada']}**\n"
            f"🚌 Veículo {result['prefixo_veiculo']}{acessivel}"
        )
    _add("assistant", msg)


# --- Render histórico ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Botões do fluxo guiado ---
step = st.session_state.step

if step == "select_line":
    by_line = st.session_state.gdata.get("by_line", {})
    nums = list(by_line.keys())
    cols = st.columns(min(len(nums), 4))
    for i, num in enumerate(nums):
        if cols[i % 4].button(f"Linha {num}", key=f"line_{num}"):
            _select_line(num)
            st.rerun()
    if st.button("Cancelar", key="cancel_line"):
        st.session_state.step = None
        st.session_state.gdata = {}
        st.rerun()

elif step == "select_direction":
    directions = st.session_state.gdata.get("directions", [])
    cols = st.columns(min(len(directions), 3))
    for i, d in enumerate(directions):
        if cols[i % 3].button(d["destino"], key=f"dir_{d['codigo_linha']}"):
            _select_direction(d)
            st.rerun()
    if st.button("Cancelar", key="cancel_dir"):
        st.session_state.step = None
        st.session_state.gdata = {}
        st.rerun()

# --- Botão de atalho (só quando idle) ---
if step is None:
    if st.button("🚌 Meu ônibus", use_container_width=False):
        _start_flow()
        st.rerun()

# --- Chat input ---
placeholder = "Qual sua localização?" if step == "get_location" else "Como posso te ajudar?"
if prompt := st.chat_input(placeholder):
    if step == "get_location":
        _fetch_arrival(prompt)
        st.rerun()
    else:
        _add("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = chat(st.session_state.messages)
            st.markdown(response)
        _add("assistant", response)
        st.rerun()
