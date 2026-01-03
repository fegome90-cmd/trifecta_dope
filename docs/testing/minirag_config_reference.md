# Mini-RAG Config Reference (Local)

This file exists to make Mini-RAG configuration discoverable via search.
It mirrors key settings from `.mini-rag/config.yaml`.

## Ollama Settings

- `ollama.connection_timeout`: seconds to establish connection
- `ollama.read_timeout`: seconds to wait for responses
- `ollama.max_retries`: retry attempts on failure
- `ollama.retry_delay`: seconds between retries
- `ollama.keep_alive`: keep connections open (true/false)

## Index Paths

- `paths.config_dir`: `.mini-rag`
- `paths.index_dir`: `.mini-rag/index`
- `paths.metadata_file`: `.mini-rag/index/metadata.json`
- `paths.embeddings_file`: `.mini-rag/index/embeddings.npy`
