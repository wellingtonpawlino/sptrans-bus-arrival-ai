from agent.agents.base import run_agent
from agent.state import AgentState
from agent.prompts.mobility import MOBILITY_PROMPT
from agent.tools.registry import MOBILITY_TOOLS


def mobility_node(state: AgentState) -> dict:
    return {"messages": run_agent(MOBILITY_PROMPT, MOBILITY_TOOLS, state["messages"])}
