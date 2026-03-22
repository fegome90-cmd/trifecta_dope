# Git Commit Signing Follow-up (2026-03-13)

## Current Decision
Disable global commit signing temporarily and treat signed commits as a follow-up feature to implement correctly later.

## Reason
Commits were failing consistently because the global Git configuration was internally inconsistent:

- `commit.gpgsign = true`
- `user.signingkey` was set to an empty value
- no usable secret OpenPGP key was available in `~/.gnupg`

This caused Git to attempt signing every commit and fail with:

- `gpg: skipped "": Invalid user ID`
- `fatal: failed to write commit object`

## Immediate Remediation Applied
Global Git configuration was adjusted to stop blocking normal commits:

```bash
git config --global --unset user.signingkey
git config --global commit.gpgsign false
```

## Current Expected State
- unsigned commits work normally
- Git no longer attempts broken GPG signing by default
- signing is explicitly deferred until a clean implementation exists

## Follow-up Feature Scope
Reintroduce commit signing as a properly configured feature.

### Option A — SSH signing
Preferred for lower operational friction on macOS/GitHub.

Tasks:
1. choose SSH signing as the standard
2. configure `gpg.format ssh`
3. set `user.signingkey` to the SSH public key path or key identifier
4. register the signing key in GitHub
5. re-enable `commit.gpgsign`
6. verify signed commits end-to-end

### Option B — OpenPGP signing
Use only if there is a specific need for classic GPG.

Tasks:
1. generate or import a real GPG secret key
2. set a valid `user.signingkey`
3. verify pinentry / agent flow locally
4. register the public key in GitHub
5. re-enable `commit.gpgsign`
6. verify signed commits end-to-end

## Acceptance Criteria for the Follow-up
1. `git commit` succeeds without `--no-gpg-sign`
2. the configured signing key is non-empty and valid
3. local verification works (`git log --show-signature`)
4. GitHub shows commits as verified
5. the chosen signing mode is documented as the default team/user setup

## Recommendation
Use SSH signing for the future implementation unless a specific OpenPGP requirement appears.
