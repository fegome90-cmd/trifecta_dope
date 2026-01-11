### Local Testing
```bash
# Validate configurations
python -m json.tool scoop/trifecta.json
python -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"

# Run tests
uv run pytest tests/unit -v
uv run pytest tests/integration -v
uv run pytest tests/acceptance -v -m "not slow"

# Run linters
uv run ruff check src/ tests/
uv run mypy src/

# Run security checks (if tools installed)
uv run bandit -r src/ -ll
```
