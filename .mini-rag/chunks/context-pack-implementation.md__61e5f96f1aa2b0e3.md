# Mostrar resultado
    if args.dry_run:
        print(f"[dry-run] Would generate Context Pack: ...")
    else:
        print(f"[ok] Context Pack generated: ...")

    if args.verbose:
        print(f"\n[verbose] Digest entries:")
        for d in pack["digest"]:
            print(f"  - {d['doc']}: {d['summary']}")
```

### Uso (Diseño Original → Comandos Actuales)

```bash
