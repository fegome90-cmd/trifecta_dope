# Security Deployment Checklist

This checklist ensures all security improvements are properly deployed and functional.

## Pre-Deployment Verification

### 1. Configuration Files
- [x] Scoop manifest (`packaging/scoop/trifecta.json`) is valid JSON
- [x] Dependabot config (`.github/dependabot.yml`) is valid YAML
- [x] CI workflow (`.github/workflows/ci.yml`) is valid YAML
- [x] Security scan workflow (`.github/workflows/security-scan.yml`) is valid YAML
- [x] Bandit configuration in `pyproject.toml`

### 2. Documentation
- [x] `SECURITY.md` created at repository root
- [x] `docs/SECURITY.md` updated with policy
- [x] `docs/security/SECURITY_IMPROVEMENTS.md` created
- [x] `packaging/scoop/README.md` created with installation instructions
- [x] Main `README.md` updated with security section

### 3. Code Quality
- [ ] No syntax errors in Python code
- [ ] All tests pass (unit, integration, acceptance)
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)

## Post-Deployment Verification

### 4. GitHub Actions Workflows
- [ ] CI workflow triggers on push to main/develop
- [ ] CI workflow triggers on pull requests
- [ ] Security scan workflow triggers on push
- [ ] Security scan workflow triggers on PRs
- [ ] Weekly scheduled scans run successfully

### 5. Dependabot
- [ ] Dependabot PRs appear for outdated dependencies
- [ ] Dependabot labels are applied correctly
- [ ] Security updates are prioritized
- [ ] Grouped updates work as configured

### 6. Security Scans
- [ ] CodeQL analysis completes successfully
- [ ] No critical or high severity issues found
- [ ] Bandit scan completes
- [ ] Safety check completes
- [ ] Secret scanning runs without errors

### 7. Scoop Manifest
- [ ] Scoop manifest available in repository
- [ ] Installation works on Windows with Scoop
- [ ] Dependencies (Python, uv) install correctly
- [ ] `trifecta --help` works after installation

## Issues to Address

### Known Issues
1. **CLI Import Error**: There's a pre-existing type annotation issue in `src/application/symbol_selector.py`:
   ```
   TypeError: src.domain.result.Ok | src.domain.result.Err is not a generic class
   ```
   This is unrelated to the security improvements and exists in the base branch.

### Required Actions
1. **Release Creation**: Create a v0.1.0 release on GitHub for Scoop manifest
2. **Hash Update**: Update Scoop manifest with actual release archive hash
3. **Testing**: Test Scoop installation on Windows system
4. **Security Email**: Set up `security-trifecta@protonmail.com` or equivalent
5. **Codecov**: Configure Codecov token for coverage reports

## Testing Commands

### Local Testing
```bash
# Validate configurations
python -m json.tool packaging/scoop/trifecta.json
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

### GitHub Actions Testing
```bash
# Check workflow syntax locally (requires act)
act -l

# Trigger workflow manually
gh workflow run ci.yml
gh workflow run security-scan.yml
```

## Rollback Plan

If issues arise:

1. **Revert Workflows**: Delete workflow files to stop automated scans
   ```bash
   git rm .github/workflows/*.yml
   git commit -m "chore: Temporarily disable workflows"
   ```

2. **Disable Dependabot**: Remove `.github/dependabot.yml`
   ```bash
   git rm .github/dependabot.yml
   git commit -m "chore: Temporarily disable Dependabot"
   ```

3. **Revert All Changes**: Reset to previous commit
   ```bash
   git revert HEAD~3..HEAD
   ```

## Monitoring

### Weekly Checks
- [ ] Review Dependabot PRs
- [ ] Check security scan results
- [ ] Review CodeQL alerts
- [ ] Update dependencies as needed

### Monthly Checks
- [ ] Audit security policy
- [ ] Review access controls
- [ ] Update documentation
- [ ] Check for new security best practices

## Sign-off

- [ ] Developer: Changes implemented and tested
- [ ] Reviewer: Code review completed
- [ ] Security: Security review completed
- [ ] Maintainer: Ready for deployment

## Notes

- All configuration files validated successfully
- Documentation is comprehensive and accurate
- Security improvements are backward compatible
- No breaking changes introduced
