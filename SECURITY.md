# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Trifecta, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Use GitHub's private security advisory feature: [Report a vulnerability](https://github.com/fegome90-cmd/trifecta_dope/security/advisories/new)
3. Or email: security-trifecta@protonmail.com (if email is preferred)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if available)
- Your contact information for follow-up

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Target**: Critical issues within 14 days, others within 30 days

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Security Features

### 1. PII Protection in Telemetry

Trifecta automatically sanitizes personally identifiable information (PII) in telemetry data:

- Absolute file paths are redacted (`<ABS_PATH_REDACTED>`)
- User directories are protected
- File URIs are sanitized

**Opt-in bypass**: Set `TRIFECTA_PII=allow` for local debugging only.

### 2. Dependency Management

- Automated dependency updates via Dependabot
- Weekly security scans using CodeQL
- Python dependency vulnerability checks with Safety

### 3. Code Security

- Static analysis with Bandit
- Secret scanning with TruffleHog
- Regular security audits

## Security Best Practices

When using Trifecta:

1. **Never commit secrets** to repository context files
2. **Review generated context** before sharing externally
3. **Use environment variables** for sensitive configuration
4. **Keep dependencies updated** using Dependabot PRs
5. **Enable telemetry PII protection** in production (default)

## Known Security Considerations

### Context File Handling

Context files (`_ctx/*.md`) may contain:
- File paths and directory structures
- Code snippets and documentation
- Project metadata

**Recommendation**: Review context files before sharing to ensure no sensitive data is included.

### Telemetry Data

Telemetry is stored locally in `_ctx/telemetry/`. To clean legacy PII:

```bash
python scripts/scrub_telemetry_pii.py ./_ctx/telemetry/events.jsonl
```

## Security Disclosure History

No security vulnerabilities have been disclosed as of January 2026.

## Contact

For security-related questions: security-trifecta@protonmail.com

For full security documentation: [docs/SECURITY.md](./docs/SECURITY.md)
