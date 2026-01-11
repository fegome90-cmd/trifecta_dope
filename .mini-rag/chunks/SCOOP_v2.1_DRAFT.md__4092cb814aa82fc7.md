## 7) Rollback + Rollout (con triggers automáticos)

**ROLLOUT**:

Estrategia: Feature flag (env var `TRIFECTA_SESSION_JSONL=1`)

Pasos:
1. Merge code with feature flag OFF by default
2. Enable in developer env (Felipe) for 1 week testing
3. Monitor telemetry for errors in `session.entry` writes
4. If stable (error rate < 0.1%), enable by default
5. Remove flag after 1 month stable operation

**ROLLBACK**:

Comando:
```bash
# Emergency rollback: disable feature flag
export TRIFECTA_SESSION_JSONL=0

# Or git revert
git log --oneline | grep "session JSONL"
git revert <commit-hash>
```

**TRIGGERS** (automáticos):

Rollback se ejecuta SI:
- Error rate de `session.entry` writes > 1% por 1 hora
- Query latency p95 > 200ms por 30 minutos
- Schema validation failures > 5% de entries
- Manual trigger: Felipe ejecuta `export TRIFECTA_SESSION_JSONL=0`

Tiempo de recovery objetivo: < 2 minutos (toggle feature flag)

**ESCAPE HATCH**:

Si rollback tarda: Usuarios pueden seguir usando session.md manual (status quo)
```bash
# Bypass: editar session.md directamente
vim _ctx/session_trifecta_dope.md
```

**DATOS/ESTADO**:

Preservado:
- Telemetry events existentes (nointouched)
- session.md existente (no deleted)

Perdido (si rollback):
- Session entries escritas durante test period (aceptable - solo dev env)

---
