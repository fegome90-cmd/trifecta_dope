### Generación Automática (JSONL → session.md)
```bash
# Script: generate_session_md.sh
trifecta session query -s . --all | \
  jq -r '"## \(.ts)\n**Type**: \(.type)\n**Summary**: \(.summary)\n**Files**: \(.files | join(", "))\n**Outcome**: \(.outcome)\n"' \
  > _ctx/session_trifecta_dope.md
```
