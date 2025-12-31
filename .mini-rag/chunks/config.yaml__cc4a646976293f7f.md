docs_glob:
  - .mini-rag/chunks/**/*.md
  - knowledge/**/*.pdf
pdf:
  enabled: true
chunking:
  chunk_size: 1400
  chunk_overlap: 0
  section_max_chars: 1400
  overlap_pct: 0.05
  source_globs:
    - docs/**/*.md
    - knowledge/**/*.md
    - knowledge/**/*.txt
    - minirag-eval/bridges/**/*.md
    - _ctx/session_trifecta_dope.md
    - .mini-rag/config.yaml
  exclude_globs:
    - docs/testing/minirag_search_bench.md
    - docs/testing/minirag_search_bench_results.md
embeddings:
  provider: ollama
  model: nomic-embed-text
retrieval:
  top_k_default: 10
  similarity_threshold: 0.5
document_policies: {}
filters: {}
paths:
  config_dir: .mini-rag
  index_dir: .mini-rag/index
  metadata_file: .mini-rag/index/metadata.json
  embeddings_file: .mini-rag/index/embeddings.npy
ollama:
  connection_timeout: 10.0
  read_timeout: 60.0
  max_retries: 5
  retry_delay: 1.0
  keep_alive: true
