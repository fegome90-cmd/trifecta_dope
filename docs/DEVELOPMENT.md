# Development Guide

## Pre-Commit Hooks

Trifecta uses pre-commit hooks to ensure code quality before commits.

### Setup

```bash
# Install pre-commit framework
pip install pre-commit
# or with uv
uv pip install pre-commit

# Install hooks to .git/hooks/
pre-commit install
```

### What Gets Checked

1. **Syntax Validation**
   - YAML/JSON syntax
   - Python AST (detects SyntaxError)
   - Trailing whitespace

2. **Linting** (Ruff - check-only, NO autofix)
   - Unused imports (F401)
   - Unused variables (F841)
   - Syntax errors (E999)

3. **Test Gate**
   - Runs acceptance tests (`-m "not slow"`)
   - Only if Python files in `src/` or `tests/` changed
   - Timeout: 30s

### Manual Run

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run test-gate --all-files
```

### Bypassing Hooks (Emergency Only)

```bash
# Skip hooks for one commit
git commit --no-verify

# Uninstall hooks
pre-commit uninstall
```

### Fixing Issues

**Unused imports detected**: Remove the import manually  
**Tests failing**: Fix the test before committing  
**Syntax error**: Fix the Python syntax issue

**Note**: Hooks are **NON-DESTRUCTIVE** - they never modify your files automatically.

---

## Testing

### Quick Test Gates

```bash
# Acceptance tests (fast)
make test-acceptance

# All tests
make test-all
```

### Manual Testing

```bash
# Unit tests
uv run pytest tests/unit

# Acceptance tests
uv run pytest tests/acceptance -m "not slow"

# With coverage
uv run pytest --cov=src tests/
```

---

## Code Quality

### Linting

```bash
# Check (no autofix)
ruff check src/ tests/

# Fix automatically (use with caution)
ruff check --fix src/ tests/
```

### Type Checking

```bash
# If mypy is configured
mypy src/
```

---

## Project Structure

```
trifecta_dope/
├── src/                    # Source code
│   ├── application/        # Use cases
│   ├── domain/             # Domain models
│   └── infrastructure/     # CLI, telemetry, LSP
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── acceptance/         # E2E acceptance tests
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```
