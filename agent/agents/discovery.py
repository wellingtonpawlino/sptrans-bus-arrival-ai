from agent.agents.base import run_agent
from agent.state import AgentState
from agent.prompts.discovery import DISCOVERY_PROMPT
from agent.tools.registry import DISCOVERY_TOOLS


def discovery_node(state: AgentState) -> dict:
    return {"messages": run_agent(DISCOVERY_PROMPT, DISCOVERY_TOOLS, state["messages"])}
