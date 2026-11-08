from agent.tools.registry import executar_ferramenta
from agent.state import AgentState


def execute_tools(state: AgentState) -> dict:
    last = state["messages"][-1]
    tool_uses = [
        b for b in last["content"]
        if hasattr(b, "type") and b.type == "tool_use"
    ]

    tool_results = [
        {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": executar_ferramenta(tool_use.name, tool_use.input),
        }
        for tool_use in tool_uses
    ]

    return {"messages": [{"role": "user", "content": tool_results}]}
