```python
def chunk_by_headings_fence_aware(
    doc_id: str,
    md: str,
    max_chars: int = 6000
) -> list[dict]:
    """
    Split markdown into chunks using headings, respecting code fences.
    """
    lines = md.splitlines()
    chunks = []

    # Estado actual
    title = "INTRO"
    title_path: list[str] = []
    level = 0
    start_line = 0
    buf: list[str] = []
    in_fence = False  # ← State machine flag

    def flush(end_line: int) -> None:
        """Flush accumulated buffer as a chunk."""
        nonlocal title, level, start_line, buf
        if buf:
            text = "\n".join(buf).strip()
            if text:
                chunks.append({
                    "title": title,
                    "title_path": title_path.copy(),
                    "level": level,
                    "text": text,
                    "start_line": start_line + 1,
                    "end_line": end_line,
                })
            buf = []
            start_line = end_line + 1

    for i, line in enumerate(lines):
        # 1. Detectar toggle de fence
        fence_match = FENCE_RE.match(line)
        if fence_match:
            in_fence = not in_fence  # Toggle estado
            buf.append(line)
            continue

        # 2. Solo procesar headings fuera de fences
        heading_match = HEADING_RE.match(line)
        if heading_match and not in_fence:
