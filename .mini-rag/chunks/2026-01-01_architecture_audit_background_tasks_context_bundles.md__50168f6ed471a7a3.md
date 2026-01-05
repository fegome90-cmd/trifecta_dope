### 4.3 `ctx_bundle_rules.yaml` (Bundle Policy v1)

```yaml
schema_version: 1

# ALLOWLIST: Solo estos paths/patterns son elegibles para bundle
allow:
  - "*.md"
  - "_ctx/context_pack.json"
  - "_ctx/session_*.md"
  - "_ctx/prime_*.md"
  - "_ctx/agent.md"
  - "skill.md"
  - "README.md"

# DENYLIST: Nunca incluir estos paths (trumps allowlist)
deny:
  - "node_modules/**"
  - ".git/**"
  - "**/*.pyc"
  - "**/__pycache__/**"
  - ".env"
  - ".env.*"
  - "**/*secret*"
  - "**/*password*"
  - "**/.venv/**"
  - "**/venv/**"

# LIMITS: Hard caps para prevenir bloat
limits:
  max_bundle_size_mb: 10
  max_file_reads: 100
  max_tool_calls: 50
  max_single_file_mb: 2

# REDACTION: Patterns a redactar en file_reads/tool_call results
redaction:
  enabled: true
  patterns:
    - 'api[_-]?key["\s:=]+[\w-]{20,}'
    - 'password["\s:=]+[^\s"]+'
    - 'token["\s:=]+[\w-]{40,}'
    - 'secret["\s:=]+[\w-]{20,}'
  replacement: "***REDACTED***"

# FAIL POLICY: Qué hacer si se viola una regla
fail_policy:
  on_deny_match: "skip_with_warning"  # skip_with_warning | fail_loudly
  on_size_exceeded: "truncate"         # truncate | fail_loudly
  on_redaction_match: "redact"         # redact | fail_loudly
```

---
