assert result.is_ok(), f"Expected Ok, got Err: {result}"
    candidate = result.unwrap()
    assert candidate.file_rel == "src/domain/__init__.py"
```
