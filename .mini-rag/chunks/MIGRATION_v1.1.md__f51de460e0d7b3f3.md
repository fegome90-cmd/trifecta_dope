### install_trifecta_context.py → DEPRECATED

**Status**: ⚠️ DEPRECATED - Kept for backward compatibility only

**Reason**: Does not follow Clean Architecture patterns (no domain layer separation)

**Migration**:
Replace all usages of:
```bash
python scripts/install_trifecta_context.py --cli-root . --segment /path
```

With:
```bash
python scripts/install_FP.py --segment /path
```

**Note**: `install_trifecta_context.py` will be removed in v2.0

---
