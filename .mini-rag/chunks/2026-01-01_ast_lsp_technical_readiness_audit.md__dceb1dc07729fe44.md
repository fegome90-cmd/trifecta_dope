### 3.3 Step 3: Progressive Logic
Update `ContextService` to:
1. Check if query looks like a symbol (`AuthManager`).
2. If yes, query `ASTParser` first.
3. If hit, return `skeleton` or `snippet` instead of full file.

---
