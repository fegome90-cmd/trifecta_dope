# Output (ambos generan estructura similar):
  ]
}
```

---

## Testing

### Cobertura de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Normalization | 3 | CRLF → LF, collapse blanks, title path |
| ID Stability | 4 | Deterministic, different doc, whitespace, case |
| Fence-Aware | 4 | Code blocks, state machine, hierarchy |
| Scoring | 4 | Keywords, level, penalties, negative |
| Preview | 3 | Collapse whitespace, truncate, ellipsis |
| Integration | 2 | Full build, stability across runs |
| Output | 1 | File written correctly |
| **Total** | **22** | |

### Ejemplo de Test

```python
def test_fence_aware_state_machine_toggle():
    """The in_fence state should toggle correctly."""
    sample = """# Intro

```python
# First block
def foo():
    pass
```
