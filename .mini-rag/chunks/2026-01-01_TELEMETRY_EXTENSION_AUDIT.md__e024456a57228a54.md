### N.4 LSP READY Definition (Canonical)

**DO NOT invent new LSP protocol requests.** Instead, observe standard notifications:

```python
# Option A: publishDiagnostics (most reliable)
if initialized AND received_first_publishDiagnostics:
    ready = True

# Option B: textDocument/definition success
if initialized AND received_first_definition_response:
    ready = True

# Pick the FIRST condition that fires
```

---
