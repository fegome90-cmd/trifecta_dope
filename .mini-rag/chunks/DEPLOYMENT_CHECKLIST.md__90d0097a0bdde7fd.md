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
