from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.llm import call_llm
from agent.nodes.tools import execute_tools


def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    content = last.get("content", [])
    if isinstance(content, list) and any(
        hasattr(b, "type") and b.type == "tool_use" for b in content
    ):
        return "tools"
    return "end"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("llm", call_llm)
    graph.add_node("tools", execute_tools)

    graph.set_entry_point("llm")

    graph.add_conditional_edges(
        "llm",
        _should_continue,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "llm")

    return graph.compile()
