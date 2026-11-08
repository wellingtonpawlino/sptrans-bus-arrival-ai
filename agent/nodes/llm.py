from anthropic import Anthropic
from dotenv import load_dotenv
from agent.prompts.system import SYSTEM_PROMPT
from agent.tools.registry import TOOLS
from agent.state import AgentState

load_dotenv()

_client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"


def call_llm(state: AgentState) -> dict:
    response = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=state["messages"],
    )
    return {"messages": [{"role": "assistant", "content": response.content}]}
