### 3. Safe Fallback (`safe_fallback`)

**Definition:** The system correctly selected fallback mode when no specific feature was expected (i.e., expected_feature == "fallback" and selected_by == "fallback").

**Formula:**
```
safe_fallback = (expected_feature == "fallback" AND selected_by == "fallback")
```

**Rationale:** Safe fallbacks indicate proper behavior for out-of-domain or general queries where no specific feature applies.
