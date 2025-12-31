```
┌─────────────────────────────────────────────────────────────┐
│  context_pack.json (written to disk)                        │
├─────────────────────────────────────────────────────────────┤
│  {                                                         │
│    "schema_version": 1,                                    │
│    "segment": "debug_terminal",                            │
│    "digest": [              // ALWAYS in prompt (~10-30 lines)│
│      {"doc": "skill", "summary": "...", "source_chunk_ids": [...]}│
│    ],                                                      │
│    "index": [               // ALWAYS in prompt (chunk refs)  │
│      {"id": "skill:a1b2...", "title_path": ["Core Rules"], ...}│
│    ],                                                      │
│    "chunks": [              // DELIVERED ON-DEMAND         │
│      {"id": "skill:a1b2...", "text": "...", ...}            │
│    ]                                                       │
│  }                                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Runtime Tool (HemDov/Agent) - SEPARATED from pack          │
├─────────────────────────────────────────────────────────────┤
│  get_context(chunk_id) → chunk["text"]                     │
│  search_context(query, k) → [chunk_id, ...]
