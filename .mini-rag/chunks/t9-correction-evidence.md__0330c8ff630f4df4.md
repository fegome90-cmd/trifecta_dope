# PROPOSED DIFF (to be implemented)
def validate_source_files(files: list[Path]) -> None:
    """Fail-closed: Reject src/* files in pack."""
    for f in files:
        if "src/" in str(f) or "/src/" in str(f):
            raise ValueError(
                f"PROHIBITED: Cannot index code files in pack: {f}\n"
                "Trifecta is PCC (meta-first), not RAG. "
                "Code access via prime links only."
            )
```

**Status:** ⚠️ PARTIAL PASS - No src/* indexed, but no explicit prohibition

---

## C) ZERO HITS → PRIME LINKS FLOW

### C.1 Test Case: "symbol extraction"

**Step 1: ctx.search**

```bash
$ trifecta ctx search --segment /Users/felipe_gonzalez/Developer/AST --query "symbol extraction" --limit 5
No results found for query: 'symbol extraction'
```

**Result:** ✅ Zero hits (expected)

**Step 2: Escalation to prime_ast.md**

```bash
$ cat /Users/felipe_gonzalez/Developer/AST/_ctx/prime_ast.md | head -50
