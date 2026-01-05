| File | Expected Format | Validation |
| :--- | :--- | :--- |
| `_ctx/prime_trifecta_dope.md` | YAML frontmatter + path list | `segment:` field exists |
| `_ctx/agent_trifecta_dope.md` | YAML frontmatter + Tech Stack | `scope:` field exists |
| `_ctx/session_trifecta_dope.md` | Session log entries | `## YYYY-MM-DD` headers |
| `_ctx/context_pack.json` | JSON Schema v1 | `schema_version: 1` |

Run: `jq '.schema_version, .segment' _ctx/context_pack.json`
Expected: `1` and `"trifecta_dope"`

---
