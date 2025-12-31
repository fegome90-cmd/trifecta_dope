# Ver estadísticas
uv run trifecta ctx stats --segment .

    if args.verbose:
        print(f"\n[verbose] Digest entries:")
        for d in pack["digest"]:
            print(f"  - {d['doc']}: {d['summary']}")
```

### Uso

```bash
