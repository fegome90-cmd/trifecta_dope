# Spec: doctor-ranking-optimization

## Requirements

### REQ-01 Doctor phrase aliases
`skill-hub` MUST map these exact weak diagnostic phrases to canonical alias `skill-hub-doctor`:
- `exit code drift`
- `no me aparecen skills`
- `hub de skills`

Scenario: when a mapped phrase is queried, output includes `Canonical alias match: skill-hub-doctor` and a `skill-hub-doctor` result before additional results.

### REQ-02 No generic hijack
Unrelated queries MUST NOT print the forced doctor canonical alias.

### REQ-03 Runtime promotion
After changing `scripts/skill-hub`, runtime promotion and verification MUST pass.
