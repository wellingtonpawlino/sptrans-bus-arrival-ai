from anthropic import Anthropic
from dotenv import load_dotenv
from agent.state import AgentState

load_dotenv()
_client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"

_TOOL = [{
    "name": "classificar_intencao",
    "description": "Classifica a intenção do usuário",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["mobility", "favorites", "discovery"],
                "description": "mobility: previsão/chegada de ônibus em tempo real. favorites: salvar/remover/listar favoritos. discovery: descobrir qual linha vai para um destino."
            }
        },
        "required": ["intent"]
    }
}]

_SYSTEM = """Classifique a intenção do usuário:
- mobility: chegada de ônibus, previsão, veículos em tempo real, "meu ônibus", "está chegando"
- favorites: salvar, remover ou listar linhas favoritas
- discovery: qual linha vai para X, que linha passa por Y, busca por destino"""


def supervisor_node(state: AgentState) -> dict:
    # Find last plain user message (not tool results)
    user_text = ""
    for m in reversed(state["messages"]):
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            user_text = m["content"]
            break

    response = _client.messages.create(
        model=MODEL,
        max_tokens=64,
        system=_SYSTEM,
        tools=_TOOL,
        tool_choice={"type": "tool", "name": "classificar_intencao"},
        messages=[{"role": "user", "content": user_text or "ajuda"}],
    )

    intent = "mobility"
    for block in response.content:
        if hasattr(block, "type") and block.type == "tool_use":
            intent = block.input.get("intent", "mobility")

    return {"intent": intent}
