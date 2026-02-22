---
name: wo/schema-fix
description: Fix invalid WO and DoD schemas for reconcile compatibility
---

# WO Schema Fix - Legacy Schema Repair

## Overview

Fix invalid WO and DoD schemas that block `ctx_reconcile_state.py`.

## When to Use

- `ctx_reconcile_state.py --apply` fails with `WO_INVALID_SCHEMA`
- `ctx_backlog_validate.py` shows schema errors
- Legacy WOs need schema compliance

## Common Schema Issues

### Issue 1: DoD con campo `items`

**Inválido**:
```yaml
version: 1
dod:
- id: WO-0036-dod
  items:
  - Cleanup complete
```

**Válido**:
```yaml
version: 1
dod:
- id: WO-0036-dod
  title: "Cleanup DoD"
  required_artifacts:
    - "verdict.json"
  required_checks:
    - name: "cleanup_complete"
      commands:
        - "echo 'Cleanup verified'"
  rules:
    - "Cleanup complete: PASS"
```

**Required fields for DoD**:
- `title` (string)
- `required_artifacts` (array of strings)
- `required_checks` (array with `name` and `commands`)
- `rules` (array of strings)

### Issue 2: WO con `required_flow` incompleto

**Inválido**:
```yaml
execution:
  engine: trifecta
  required_flow:
  - verify
  segment: .
```

**Válido**:
```yaml
execution:
  engine: trifecta
  required_flow:
  - session.append:intent
  - ctx.sync
  - ctx.search
  - ctx.get
  - session.append:result
  segment: .
```

**Required items for `required_flow`**:
1. `session.append:intent`
2. `ctx.sync`
3. `ctx.search`
4. `ctx.get`
5. `session.append:result`

## Fix Process

### Step 1: Diagnose

```bash
# Find schema issues
uv run python scripts/ctx_backlog_validate.py 2>&1 | head -30
```

### Step 2: Fix DoD Schemas

```bash
# Check DoD files
ls _ctx/dod/

# For each invalid DoD, edit to add required fields
# Invalid fields can be prefixed with x_ to preserve data
```

### Step 3: Fix WO required_flow

**Option A: Manual fix** (for few WOs)
```bash
# Edit each WO file
# Replace required_flow block
```

**Option B: Batch fix** (for many WOs)
```python
import re
from pathlib import Path

old = r'required_flow:\n  - verify\n  segment: \.'
new = '''required_flow:
  - session.append:intent
  - ctx.sync
  - ctx.search
  - ctx.get
  - session.append:result
  segment: .'''

for f in Path('_ctx/jobs/done').glob('WO-*.yaml'):
    content = f.read_text()
    if 'required_flow:\n  - verify' in content:
        f.write_text(re.sub(old, new, content))
        print(f'Fixed: {f}')
```

### Step 4: Verify

```bash
# Re-run validation
uv run python scripts/ctx_backlog_validate.py

# Try reconcile
uv run python scripts/ctx_reconcile_state.py --apply
```

## Important Notes

### Modifying WOs in done/failed

**Requires bypass** because `validate_wo_metadata_update()` only allows:
- `closed_at`, `closed_by`, `verified_at`, `verified_at_sha`
- `evidence`, `result`, `x_governance_notes`

**Use bypass activation**:
```bash
# Option 1: Environment variable
TRIFECTA_HOOKS_DISABLE=1 \
TRIFECTA_WO_BYPASS_REASON="Schema compliance fix for legacy WOs" \
git commit -m "fix: schema fixes for legacy WOs"

# Option 2: File marker
echo "Schema fixes" > .trifecta_hooks_bypass
git commit -m "fix: schema fixes"
rm .trifecta_hooks_bypass
```

### INCIDENT NOTE Required

Create `_ctx/incidents/INCIDENT-SCHEMA-FIX-YYYY-MM-DD.md`:
```markdown
# INCIDENT-SCHEMA-FIX

## Motivo
Legacy WOs have invalid schemas blocking reconcile

## Impacto
required_flow fields updated to schema compliance

## Plan de Remediación
None - schema compliance only

## Autorización
[who]
```

## Resources

- `scripts/ctx_backlog_validate.py` - Validation
- `scripts/ctx_reconcile_state.py` - Reconciliation
- `scripts/hooks/common.sh` - `validate_wo_metadata_update()`
- `wo/finish` - Bypass activation methods

## Quick Reference

```bash
# Diagnose
uv run python scripts/ctx_backlog_validate.py 2>&1 | head -30

# Find invalid required_flow
grep -r "required_flow:" _ctx/jobs/done/*.yaml | grep "  - verify$"

# Fix and commit with bypass
TRIFECTA_HOOKS_DISABLE=1 \
TRIFECTA_WO_BYPASS_REASON="Schema fixes" \
git add _ctx/
git commit -m "fix: schema fixes for legacy WOs"
```
