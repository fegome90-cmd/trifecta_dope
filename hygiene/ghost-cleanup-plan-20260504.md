# Ghost Config Cleanup Plan — 2026-05-04

## Summary
- **Total branch.* config entries**: 19 (for 10 branches)
- **Local branches that exist**: 1 (main)
- **Ghost entries**: 18 (for 9 deleted local branches)

## Ghost Entries (config exists, local branch deleted)

### 1. feat/wo-WO-0011
```bash
git config --unset branch.feat/wo-WO-0011.remote
git config --unset branch.feat/wo-WO-0011.merge
```

### 2. codex/chore-wo-hygiene
```bash
git config --unset branch.codex/chore-wo-hygiene.remote
git config --unset branch.codex/chore-wo-hygiene.merge
```

### 3. codex/ci-main-unblock
```bash
git config --unset branch.codex/ci-main-unblock.remote
git config --unset branch.codex/ci-main-unblock.merge
```

### 4. codex/wo-hygiene-rebase
```bash
git config --unset branch.codex/wo-hygiene-rebase.remote
git config --unset branch.codex/wo-hygiene-rebase.merge
```

### 5. codex/wo-guard-wave1
```bash
git config --unset branch.codex/wo-guard-wave1.remote
git config --unset branch.codex/wo-guard-wave1.merge
```

### 6. codex/wo-take-immediate-validation
```bash
git config --unset branch.codex/wo-take-immediate-validation.remote
git config --unset branch.codex/wo-take-immediate-validation.merge
```

### 7. codex/chore-wo-hygiene-safe
```bash
git config --unset branch.codex/chore-wo-hygiene-safe.remote
git config --unset branch.codex/chore-wo-hygiene-safe.merge
```

### 8. codex/merge-trifecta-wo-sidecar-hardening
```bash
git config --unset branch.codex/merge-trifecta-wo-sidecar-hardening.remote
git config --unset branch.codex/merge-trifecta-wo-sidecar-hardening.merge
```

### 9. codex/main-consolidation
```bash
git config --unset branch.codex/main-consolidation.remote
git config --unset branch.codex/main-consolidation.merge
```

## Safe to Keep
- `branch.main.remote=origin` ✅
- `branch.main.vscode-merge-base=origin/main` ✅
- `branch.main.merge=refs/heads/main` ✅

## Execution Notes
- **DO NOT execute these commands without human confirmation**
- Backup already saved to `hygiene/ghost-entries-backup-20260504.txt`
- These are local-only config entries (not affecting remote)
- Safe to remove — no data loss, only cleanup tracking config
