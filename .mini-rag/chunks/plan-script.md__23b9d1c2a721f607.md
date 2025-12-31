def build_pack(md_paths, out_path="context_pack.json"):
    docs = []
    all_chunks = []
    for p in md_paths:
        path = Path(p)
        doc_id = path.stem
        md = normalize(path.read_text(encoding="utf-8"))
        chunks = chunk_by_headings(doc_id, md)
        docs.append({
            "doc": doc_id,
            "file": path.name,
            "sha256": sha256_text(md),
            "chunk_count": len(chunks),
        })
        all_chunks.extend(chunks)

    index = [
        {
            "id": c["id"],
            "doc": c["doc"],
            "title": c["title"],
            "level": c["level"],
            "preview": preview(c["text"]),
        }
        for c in all_chunks
    ]
