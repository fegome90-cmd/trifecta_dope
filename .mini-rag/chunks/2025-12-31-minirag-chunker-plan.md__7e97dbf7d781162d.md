```python
def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def iter_source_files(config: dict) -> Iterable[Path]:
    chunking = config.get("chunking", {})
    source_globs = chunking.get("source_globs", [])
    for pattern in source_globs:
        for path in Path(".").glob(pattern):
            if path.is_file():
                yield path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=".mini-rag/chunks")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    chunking = config.get("chunking", {})
    rules = ChunkRules(
        chunk_size=int(chunking.get("chunk_size", 800)),
        section_max_chars=int(chunking.get("section_max_chars", 1400)),
        overlap_pct=float(chunking.get("overlap_pct", 0.05)),
    )
    chunks: List[Chunk] = []
    for file_path in iter_source_files(config):
        if file_path.suffix.lower() not in {".md", ".markdown", ".txt"}:
            continue
        text = file_path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(text, rules, str(file_path)))

    write_chunks(chunks, Path(args.output_dir))


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**
