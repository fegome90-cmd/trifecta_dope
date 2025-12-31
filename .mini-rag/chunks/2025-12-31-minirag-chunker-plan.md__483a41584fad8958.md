break
            start += step

    for block in blocks:
        if block.kind == "heading" and block.heading_level is not None:
            flush_section()
            level = min(block.heading_level, 3)
            title_path = title_path[: level - 1]
            title_path.append(block.heading_text or "")
            section_blocks.append(block)
            continue
        section_blocks.append(block)

    flush_section()
    return chunks


def chunk_markdown(text: str, rules: ChunkRules, source_path: str) -> List[Chunk]:
    normalized = normalize_markdown(text)
    blocks = parse_markdown(normalized)
    return chunk_blocks(blocks, rules, source_path)
```
