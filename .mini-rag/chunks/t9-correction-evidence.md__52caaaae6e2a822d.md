# scripts/ingest_trifecta.py
   def validate_source_files(files: list[Path]) -> None:
       for f in files:
           if "src/" in str(f) or "/src/" in str(f):
               raise ValueError(
                   f"PROHIBITED: Cannot index code files: {f}\n"
                   "Trifecta is PCC (meta-first), not RAG."
               )
   ```

2. **Improve routing accuracy** (OPTIONAL):
   - Add 2-3 aliases for common zero-hit queries
   - Target: "integration" → prime_ast.md
   - Target: "symbol extraction" → prime_ast.md

### RESIDUAL RISKS

1. **No automated ctx.open:** Prime links are manual (agent must read prime, extract path, open file)
2. **Session raw mode exceeds budget:** Mitigated by using excerpt mode by default
3. **Routing accuracy below target:** 75% vs 80%, but zero hits are acceptable behavior

---

## FINAL NOTES

**Evidence-only mode:** ✅ All claims backed by command outputs
**No gaming metrics:** ✅ Used fixed definitions (routing accuracy, budget compliance)
**Reproducible:** ✅ All commands copy/paste ready
**Fail-closed:** ⚠️ Missing explicit prohibition (must fix)

**Next Steps:**
1. Implement fail-closed prohibition in `ingest_trifecta.py`
2. Add 2-3 routing aliases for common queries
3. Document ctx.open workflow (future T9.B)
