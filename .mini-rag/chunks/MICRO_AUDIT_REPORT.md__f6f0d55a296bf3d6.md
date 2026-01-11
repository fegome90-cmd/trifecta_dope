### 🥇 1. Error Classification by Type (P0 #1)
**Ahorro esperado**: 4-6 hours/sprint in debugging "wrong error card shown"  
**Esfuerzo**: 30 min  
**Riesgo si no se hace**: Silent regression breaks agent error handling

```bash
# Commands to implement
# 1. Update cli.py to catch PrimeFileNotFoundError by type
# 2. Add tripwire test
# 3. Remove fallback_prime_missing_string_match_used deprecation path
```

---
