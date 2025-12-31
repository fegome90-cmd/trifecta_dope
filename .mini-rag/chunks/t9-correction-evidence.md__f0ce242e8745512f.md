# Expected: Retrieved 1 chunk(s) (mode=excerpt, tokens=~195)
```

### Test 4: Verify Pack Contents

```bash
cat /Users/felipe_gonzalez/Developer/AST/_ctx/context_pack.json | python3 -c "import json, sys; pack = json.load(sys.stdin); print(f'Total chunks: {len(pack[\"chunks\"])}'); [print(f'{i+1}. {c[\"id\"]} - {c[\"title_path\"][0]}') for i, c in enumerate(pack['chunks'])]"
