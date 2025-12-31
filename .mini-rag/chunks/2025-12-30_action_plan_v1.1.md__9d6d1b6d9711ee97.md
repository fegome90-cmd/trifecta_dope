### Root Cause
Two indexing rules are capturing the same file:
1. **Primary rule**: Index `skill.md` as doc type `skill`
2. **Fallback rule**: Index all `.md` as references (`ref:<filename>`)
