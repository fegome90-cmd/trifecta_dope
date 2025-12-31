## Why This is Better

| Aspect | Complex (PCC/RAG) | Simple (Heuristic) |
|--------|-------------------|-------------------|
| **Complexity** | High (chunking, scoring, LLM) | Low (keyword matching) |
| **Token usage** | ~2000 (chunks) | ~3000 (complete files) |
| **Accuracy** | May miss context | Complete coverage |
| **Latency** | High (LLM orchestrator) | Low (instant) |
| **Maintenance** | Complex (scoring tuning) | Simple (keyword rules) |
| **Agent support** | HemDov-specific | Any agent |

**For 5 small files, simple is better.**

---
