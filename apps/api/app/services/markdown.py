import re

FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")


def fenced_line_flags(lines: list[str]) -> list[bool]:
    """Para cada linha, True se pertence a uma cerca ``` ou ~~~ (inclusive as linhas da cerca)."""
    flags: list[bool] = []
    fence: str | None = None
    for line in lines:
        if fence is None:
            opened = FENCE_OPEN_RE.match(line)
            if opened:
                fence = opened.group(1)
                flags.append(True)
            else:
                flags.append(False)
            continue
        flags.append(True)
        closed = FENCE_CLOSE_RE.match(line)
        if closed and closed.group(1)[0] == fence[0] and len(closed.group(1)) >= len(fence):
            fence = None
    return flags


def mask_fences(text: str) -> str:
    lines = text.split("\n")
    flags = fenced_line_flags(lines)
    return "\n".join(" " * len(line) if fenced else line for line, fenced in zip(lines, flags))
