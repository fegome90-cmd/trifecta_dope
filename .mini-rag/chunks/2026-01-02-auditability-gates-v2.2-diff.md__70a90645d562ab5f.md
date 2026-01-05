["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # v2.2: Mensaje de error más útil si sync falla
    if result.returncode != 0:
        print(f"=== SYNC STDOUT ===")
        print(result.stdout)
        print(f"=== SYNC STDERR ===")
        print(result.stderr)

    assert result.returncode == 0, f"sync failed: {result.stderr}"

    pack_path = ctx_dir / "context_pack.json"
    assert pack_path.exists(), "context_pack.json not created"

    content = pack_path.read_text()

    # v2.2: Assertions con mensajes útiles
    assert "/Users/" not in content, f"PII leak /Users/ found in first 500 chars: {content[:500]}"
    assert "/home/" not in content, f"PII leak /home/ found"
    assert "file://" not in content, f"file:// URI found"
```
