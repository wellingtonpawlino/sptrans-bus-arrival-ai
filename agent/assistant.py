from agent.graph import build_graph

_graph = build_graph()


def chat(messages: list[dict]) -> str:
    result = _graph.invoke({"messages": messages})
    last = result["messages"][-1]
    content = last.get("content", [])
    if isinstance(content, list):
        for block in content:
            if hasattr(block, "text"):
                return block.text
    return str(content)
