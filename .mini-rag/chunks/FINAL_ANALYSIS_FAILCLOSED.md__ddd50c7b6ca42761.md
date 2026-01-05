### BLOCKER #4: Token vs Bytes (Ambigüedad de Spec)
**Causa**: "40% reducción" usa `wc -w` (words ≠ tokens), no especifica tokenizer  
**Evidencia**: AUDIT:L316-L356, FINAL_PROPOSAL:L48 ("~40%")  
**Fix mínimo**: Decidir bytes (simple) o tokens (especificar tokenizer: tiktoken/gpt-4)  
**Test/Gate**: Script de medición determinista

---
