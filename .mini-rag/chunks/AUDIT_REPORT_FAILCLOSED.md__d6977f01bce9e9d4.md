```python
import subprocess
import re

def test_session_query_no_absolute_paths():
    """Verify session query output contains no absolute paths."""
    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--last", "5"],
        capture_output=True, text=True, check=True
    )

    # Patterns to detect
    patterns = [
        r"/Users/\w+",
        r"/home/\w+",
        r"C:\\Users\\\w+",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, result.stdout)
        assert not matches, f"❌ Found absolute paths: {matches}"

    print("✅ No privacy leaks detected")

def test_session_query_no_secrets():
    """Verify output contains no API keys or tokens."""
    result = subprocess.run(
        ["uv", "run", "trifecta", "session", "query", "-s", ".", "--all"],
        capture_output=True, text=True, check=True
    )

    # Patterns for common secrets
    patterns = [
        r"API_KEY=\w+",
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
        r"GEMINI_API_KEY",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, result.stdout, re.IGNORECASE)
        assert not matches, f"❌ Found secrets: {matches}"

    print("✅ No secrets leaked")
```

---
