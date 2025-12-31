## Anti-Thesaurus Compliance

| Constraint | Status | Evidence |
|------------|--------|----------|
| No 1-word triggers for broad features | ✅ PASS | All triggers have phrase (min 2 words) |
| high_signal only for specific terms | ✅ PASS | Used only for "ctx stats", "events.jsonl", "SearchUseCase", etc. |
| No embedding/semantic search | ✅ PASS | Pure keyword matching with >=2 terms required |
| No src/ indexing by default | ✅ PASS | Only allowlisted paths in feature bundles |
| aliases.yaml maps to feature_id | ✅ PASS | Not to free text - each alias resolves to specific feature |

---
