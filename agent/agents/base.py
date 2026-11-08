from anthropic import Anthropic
from dotenv import load_dotenv
from agent.tools.registry import executar_ferramenta

load_dotenv()
_client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"


def run_agent(system_prompt: str, tools: list, messages: list) -> list:
    """Runs tool-calling loop, returns only new messages added."""
    current = list(messages)
    while True:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=current,
        )
        current.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": b.id,
                "content": executar_ferramenta(b.name, b.input),
            }
            for b in response.content
            if hasattr(b, "type") and b.type == "tool_use"
        ]
        current.append({"role": "user", "content": tool_results})
    return current[len(messages):]
