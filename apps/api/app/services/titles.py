import re

from app.services.markdown import fenced_line_flags

TITLE_MAX = 160
UNTITLED = "Sem título"
HEADING_RE = re.compile(r"^#{1,6} (.*)$")


def first_heading(content_md: str) -> str:
    lines = content_md.split("\n")
    for line, fenced in zip(lines, fenced_line_flags(lines)):
        if fenced:
            continue
        match = HEADING_RE.match(line.rstrip("\r"))
        if match:
            text = match.group(1).strip()[:TITLE_MAX]
            if text:
                return text
    return ""


def effective_title(title: str | None, content_md: str) -> str:
    cleaned = (title or "").strip()
    if cleaned:
        return cleaned[:TITLE_MAX]
    return first_heading(content_md) or UNTITLED
