## Invariant Keys (v=1)

Every PD_REPORT line **always** includes these 7 key-value pairs:

| Key | Type | Description |
|-----|------|-------------|
| `v` | int | Contract version (currently `1`) |
| `stop_reason` | string | Why retrieval stopped: `complete`, `budget`, `max_chunks`, `evidence`, `error` |
| `chunks_returned` | int | Number of chunks actually returned |
| `chunks_requested` | int | Number of chunks requested |
| `chars_returned_total` | int | Total characters returned across all chunks |
| `strong_hit` | 0\|1 | Evidence detection: query matches chunk title/ID (word boundary) AND chunk kind is `prime` |
| `support` | 0\|1 | Evidence detection: chunk text contains strict code definition patterns (`def <query>(`, `class <query>:`, etc.) with guards to avoid false positives |
