### C.1) Latencia measurement (SCOOP sección 3, métrica 1)

**Propuesta SCOOP**:
```bash
for i in {1..100}; do
  time uv run trifecta session query -s . --last 5 2>&1 | grep real
done | awk '{print $2}' | sort -n | tail -n 5 | head -n 1
```

**PROBLEMAS**:
1. ❌ `time` output no es parseable deterministicamente (varía entre shells)
2. ❌ No computa p95 correctamente (awk logic es aproximado)
3. ❌ No genera output JSON (no integrable en CI)
4. ❌ Dataset no está especificado (¿10K events? ¿50K?)

**FIX REQUERIDO**: Script Python determinista

**BLOCKER #3**: Crear `scripts/bench_session_query.py`:
