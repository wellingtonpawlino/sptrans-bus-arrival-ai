from anthropic import Anthropic
from dotenv import load_dotenv
from agent.prompts.system import SYSTEM_PROMPT
from agent.tools.registry import TOOLS, executar_ferramenta

load_dotenv()

client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"


def chat(messages: list[dict]) -> str:
    working_messages = list(messages)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=working_messages,
    )

    while response.stop_reason == "tool_use":
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        working_messages.append({"role": "assistant", "content": response.content})

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": executar_ferramenta(tool_use.name, tool_use.input),
            }
            for tool_use in tool_uses
        ]

        working_messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=working_messages,
        )

    return next(b.text for b in response.content if hasattr(b, "text"))
