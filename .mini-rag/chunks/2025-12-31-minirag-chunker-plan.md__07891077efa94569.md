d="paragraph", text="".join(buf)))
            buf = []

    for line in md.splitlines(keepends=True):
        stripped = line.lstrip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        if is_fence:
            marker = stripped[:3]
            if not in_fence:
                flush_paragraph()
                in_fence = True
                fence_marker = marker
                buf = [line]
                continue
            if fence_marker is None or marker == fence_marker:
                buf.append(line)
                blocks.append(Block(kind="fence", text="".join(buf)))
                buf = []
                in_fence = False
                fence_marker = None
                continue

        if in_fence:
            buf.append(line)
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped.split(" ", 1)[0])
            heading_text = stripped[level:].strip()
            blocks.append(
                Block(kind="heading", text=line, heading_level=level, heading_text=heading_text)
            )
            continue

        if stripped.strip() == "":
            buf.append(line)
            flush_paragraph()
            continue

        buf.append(line)

    flush_paragraph()
    return blocks


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("u
