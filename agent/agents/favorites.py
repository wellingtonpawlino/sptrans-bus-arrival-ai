from agent.agents.base import run_agent
from agent.state import AgentState
from agent.prompts.favorites import FAVORITES_PROMPT
from agent.tools.registry import FAVORITES_TOOLS


def favorites_node(state: AgentState) -> dict:
    return {"messages": run_agent(FAVORITES_PROMPT, FAVORITES_TOOLS, state["messages"])}
