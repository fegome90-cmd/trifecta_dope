---
name: hardcoded-secrets
enabled: true
event: file
pattern: (api_key\s*=\s*["\']|password\s*=\s*["\']|secret\s*=\s*["\']|token\s*=\s*["\']|sk-[a-zA-Z0-9]{20,})
action: block
---

🚫 **SECURITY: Hardcoded Secret Detected**

**BLOCKED**: You're about to commit a hardcoded secret.

**Remediation:**
1. Remove the secret immediately
2. Use environment variables
3. Rotate the compromised secret
4. Add to pre-commit hooks

**This violation will be logged to Obsidian on next sync.**
