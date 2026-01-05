#### Corto Plazo (Sprints 1-2)
1. **Score-based Auto PD**
   ```python
   def get(self, ..., auto_mode=True):
       if auto_mode and score < 0.6:
           mode = "skeleton"  # L0 auto
   ```

2. **LSP Real Output**
   ```python
   # En hover, retornar resultado real de LSP
   if result := client.request("textDocument/hover", ...):
       return ASTResponse(kind="lsp", data=result)
   ```
