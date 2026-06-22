def estimate_tokens(text: str) -> int:
    """Return a simple dependency-free token estimate.

    Most English/code prompts average around 3-5 chars per token. We use 4 and
    round up so the estimate is useful without requiring tiktoken.
    """
    if not text:
        return 0
    return (len(text) + 3) // 4
