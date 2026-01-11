# Remediation Plan: WO-0019 Technical Debt & System Hygiene

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve critical blocking technical debt (GGA hooks) and restore system hygiene (dependencies, documentation consistency) identified in WO-0019 debrief.

**Architecture:** Systematic remediation following "Fail-Closed" principles. Critical path first (hooks), then quality standards (coverage), then documentation hygiene.

**Tech Stack:** `git`, `npm`, `yaml`, `trifecta`

---

### Task 1: Fix Critical GGA Hooks (P0)

**Files:**
- Modify: `.husky/pre-commit` (if exists)
- Modify: `.husky/pre-push` (if exists)

**Step 1: Check for existence of Husky hooks**

```bash
ls -F .husky/pre-commit .husky/pre-push || echo "Husky hooks not found, checking git hooks"
```

**Step 2: Disable 'gga run' in pre-commit (if present)**

If `.husky/pre-commit` exists and contains `gga run`:

```bash
sed -i 's/^gga run/# gga run  # TODO: Enable when GGA is implemented/g' .husky/pre-commit
```

**Step 3: Disable 'gga run' in pre-push (if present)**

If `.husky/pre-push` exists and contains `gga run`:

```bash
sed -i 's/^gga run/# gga run  # TODO: Enable when GGA is implemented/g' .husky/pre-push
```

**Step 4: Verify git hooks do not fail**

```bash
# Dry run commit (should not fail with 127)
git commit --dry-run
```

**Step 5: Commit changes**

```bash
git add .husky/pre-commit .husky/pre-push 2>/dev/null || true
git commit -m "fix(hooks): disable missing gga command to unblock workflow" || echo "No hooks modified"
```

---

### Task 2: Fix Missing Coverage Dependency (P1)

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`

**Step 1: Verify current state**

```bash
npm list @vitest/coverage-v8 || echo "Package missing"
```

**Step 2: Install dependency**

```bash
npm install -D @vitest/coverage-v8
```

**Step 3: Verify installation**

```bash
grep "@vitest/coverage-v8" package.json
```

**Step 4: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore(deps): add @vitest/coverage-v8 for test metrics"
```

---

### Task 3: Documentation Hygiene & Mismatches (P2)

**Files:**
- Modify: `_ctx/jobs/pending/WO-0019.yaml` (or relevant location)
- Create: `_ctx/jobs/pending/WO-0020-formatter.yaml`
- Create: `_ctx/jobs/pending/WO-0021-verdict-generator.yaml`

**Step 1: Correct WO-0019 JSON reference**

Find where `WO-0019.yaml` is (search first) and correct `infra_config.yaml` to `infra_config.json`.

```bash
# Locate file
find _ctx/jobs -name "*WO-0019.yaml"

# Replace content
sed -i 's/infra_config.yaml/infra_config.json/g' _ctx/jobs/pending/WO-0019.yaml
```

**Step 2: Create WO-0020 for Prettier Formatting**

```bash
cat > _ctx/jobs/pending/WO-0020-formatter.yaml <<EOF
title: Format documentation files with Prettier
status: pending
priority: medium
description: "Fix formatting issues in 62 files identified in WO-0019 debrief."
steps:
  - "Run npm run format on all docs"
  - "Verify clean diffs"
EOF
```

**Step 3: Create WO-0021 for Verdict Generator**

```bash
cat > _ctx/jobs/pending/WO-0021-verdict-generator.yaml <<EOF
title: Implement Missing Verdict Generator (WO-0005)
status: pending
priority: medium
description: "Implement verdict_generator.sh for MELT metrics generation."
context: "WO-0005 was skipped. Re-evaluate if validation_report.txt supersedes this."
steps:
  - "Analyze need for verdict_generator.sh"
  - "Implement or deprecate formally"
EOF
```

**Step 4: Commit**

```bash
git add _ctx/jobs/pending/*.yaml
git commit -m "docs: fix WO-0019 references and create WOs for technical debt"
```
