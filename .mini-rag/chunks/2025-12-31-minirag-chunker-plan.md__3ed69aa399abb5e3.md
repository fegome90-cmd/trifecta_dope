urce_path=source_path,
                title_path=list(title_path),
                char_count=len(normalized),
                chunk_hash=chunk_hash,
                doc=doc,
            )
        )

    def _append_fallback(section: Sequence[Block]) -> None:
        paragraphs = _split_paragraphs(section)
        buffer: List[str] = []
        buffer_len = 0
        for para in paragraphs:
            if len(para) > rules.chunk_size:
                if buffer:
                    _append_chunk("".join(buffer))
                    buffer = []
                    buffer_len = 0
                _split_large_paragraph(para)
                continue
            if buffer_len + len(para) > rules.chunk_size and buffer:
                _append_chunk("".join(buffer))
                buffer = []
                buffer_len = 0
            buffer.append(para)
            buffer_len += len(para)
        if buffer:
            _append_chunk("".join(buffer))

    def _split_large_paragraph(text: str) -> None:
        overlap = max(1, int(rules.chunk_size * min(rules.overlap_pct, 0.05)))
        step = max(1, rules.chunk_size - overlap)
        start = 0
        while start < len(text):
            end = min(start + rules.chunk_size, len(text))
            _append_chunk(text[start:end])
            if end >= len(text):
                break
            start += step

    for block in blocks:
