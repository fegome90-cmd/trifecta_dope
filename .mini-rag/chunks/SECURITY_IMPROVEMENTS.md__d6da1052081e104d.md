### Configuration
```toml
[tool.bandit]
exclude_dirs = ["tests", "scripts/debug", ".venv", "venv"]
skips = ["B101"]  # Skip assert_used in non-test code

[tool.bandit.assert_used]
skips = ["*_test.py", "test_*.py"]
```
