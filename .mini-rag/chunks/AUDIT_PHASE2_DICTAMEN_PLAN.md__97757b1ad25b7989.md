### 1) Docs vs Runtime (PATH HYGIENE)
- **Doc dice**: "Audit: No PII, No VFS, Sanitized Paths" (`agent_trifecta_dope.md` line 69)
- **Runtime hace**: Escribe `/Users/felipe_gonzalez/Developer/agent_h` en `context_pack.json`
- **Evidencia**: `grep -n "repo_root.*Users" _ctx/context_pack.json` retorna matches
