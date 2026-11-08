from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.agents.supervisor import supervisor_node
from agent.agents.mobility import mobility_node
from agent.agents.favorites import favorites_node
from agent.agents.discovery import discovery_node


def _route(state: AgentState) -> str:
    return state.get("intent", "mobility")


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("mobility", mobility_node)
    graph.add_node("favorites", favorites_node)
    graph.add_node("discovery", discovery_node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route,
        {"mobility": "mobility", "favorites": "favorites", "discovery": "discovery"},
    )
    graph.add_edge("mobility", END)
    graph.add_edge("favorites", END)
    graph.add_edge("discovery", END)
    return graph.compile()
