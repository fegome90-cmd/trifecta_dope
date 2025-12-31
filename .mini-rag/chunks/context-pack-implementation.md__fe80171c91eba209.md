```python
class ContextPackBuilder:
    """Builds token-optimized Context Pack from markdown files."""

    def __init__(self, segment: str, repo_root: Path):
        self.segment = segment
        self.repo_root = repo_root
        self.segment_path = repo_root / segment

    def build(self, output_path: Path | None = None) -> dict:
        """
        Build complete Context Pack.
        """
        # 1. Encontrar archivos markdown
        md_files = self.find_markdown_files()

        # 2. Procesar cada documento
        docs = []
        all_chunks = []
        for path in md_files:
            doc_id, content = self.load_document(path)
            chunks = self.build_chunks(doc_id, content, path)

            docs.append({
                "doc": doc_id,
                "file": path.name,
                "sha256": sha256_text(content),
                "chunk_count": len(chunks),
                "total_chars": len(content),
            })
            all_chunks.extend(chunks)

        # 3. Construir índice
        index = []
        for chunk in all_chunks:
            title = " → ".join(chunk["title_path"]) if chunk["title_path"] else "Introduction"
            index.append({
                "id": chunk["id"],
                "doc": chunk["doc"],
                "title_path": chunk["title_path"],
                "preview": preview(chunk["text"]),
                "token_est"
