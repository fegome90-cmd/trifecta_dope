# Contradiction Probes

Goal: ensure queries that assert incorrect claims retrieve the explicit "NO" statements.

Expected sources (top-5):
- "trifecta usa embeddings": `README.md` (section "NO SOMOS") or equivalent doc.
- "trifecta es un rag": `README.md` (section "NO SOMOS").
- "mini-rag es parte de trifecta": `README.md` (Mini-RAG is external tool).
- "trifecta usa busqueda lexical": `README.md` (lexical search note).
- "trifecta indexa todo el repo": `README.md` (prohibitions).

Pass criteria:
- 4/5 queries include a denial or correction in top-5.
- Accept `minirag-eval/bridges/all_bridges.md` as PASS when present.
