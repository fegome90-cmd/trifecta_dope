### Rule #4: LSP READY = initialize + (diagnostics OR definition success)
```python
# ✅ READY states:
# 1. Received publishDiagnostics notification after initialize
# 2. Received successful definition response after initialize

# ❌ NOT READY:
# Don't invent custom LSP requests (e.g., textDocument/diagnostics)
```

---
