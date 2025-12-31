_hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _split_paragraphs(blocks: Sequence[Block]) -> List[str]:
    paragraphs: List[str] = []
    for block in blocks:
        if block.kind == "heading":
            paragraphs.append(block.text)
            continue
        paragraphs.append(block.text)
    return paragraphs


def chunk_blocks(blocks: Sequence[Block], rules: ChunkRules, source_path: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    seen_hashes: set[str] = set()
    title_path: List[str] = []
    section_blocks: List[Block] = []

    def flush_section() -> None:
        nonlocal section_blocks, chunks
        if not section_blocks:
            return
        section_text = "".join(b.text for b in section_blocks)
        if len(section_text) <= rules.section_max_chars:
            _append_chunk(section_text)
        else:
            _append_fallback(section_blocks)
        section_blocks = []

    def _append_chunk(text: str) -> None:
        normalized = text.strip() + "\n"
        chunk_hash = _hash_text(normalized)
        if chunk_hash in seen_hashes:
            return
        seen_hashes.add(chunk_hash)
        doc = os.path.basename(source_path)
        chunks.append(
            Chunk(
                text=normalized,
                source_path=source_path,
                title_path=list(title_path),
