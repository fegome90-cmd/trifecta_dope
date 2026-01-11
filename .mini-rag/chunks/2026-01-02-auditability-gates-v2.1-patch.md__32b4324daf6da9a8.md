pack.sanitized_dump()

    # Paths relativos NO deben ser redactados
    assert "some/relative/path" in json_str or "some_relative_path" in json_str or "<RELATIVE>" in json_str
```
