# Closed-PR Semantic Memo — Correction Report

> **Date**: 2026-05-09
> **Scope**: Documentation-only. No operational Git changes.
> **Related**: `closed-pr-semantic-memo-20260509.md` (original memo)
> **Authority**: See `git-hygiene-document-authority-20260509.md`

---

## 1. Correction Summary

This report documents corrections applied to `closed-pr-semantic-memo-20260509.md` to resolve a contradiction: the memo presented Rule 5 as an absolute fail-safe ("en caso de duda = PRESERVED") while simultaneously documenting three DELETED branches with acknowledged uncertainty.

**Why**: An absolute fail-safe rule is appropriate prospectively (before deletion), but presenting post-hoc deletes with incomplete evidence as "safe" is misleading. The honest classification is **accepted residual risk**.

---

## 2. Changes Applied

| Change | Location | Before | After |
|--------|----------|--------|-------|
| Evidence strength column | Section 3 (DELETED branches) | Not present | Added `Evidence strength` field to each DELETED branch table: HIGH, MEDIUM-LOW, LOW-MEDIUM |
| Rule 5 reformulation | Section 4, Regla 5 | "En caso de duda = PRESERVED (default)" — absolute fail-safe | Fail-safe is prospective only. For already-deleted branches with documented uncertainty: classify as **accepted residual risk** |
| Accepted Residual Risk section | New Section 5 | Not present | Added table listing all 3 DELETED branches with their evidence strength, accepted risk, and reversibility |
| Section renumbering | Sections 5→6, 6→7, 7→8 | Old numbering | Sections renumbered to accommodate new section |

---

## 3. Contradiction Corrected

| Contradiction | Resolution |
|---------------|------------|
| Rule 5 stated "duda = PRESERVED" as an absolute, but 3 branches were DELETED with documented uncertainty (especially `codex/docs-skillhub-context-refresh-20260327` where commit-by-commit overlap was not verified) | Rule 5 now distinguishes: (a) **prospective** decisions → duda must incline to PRESERVED, (b) **post-hoc** classification of already-deleted branches with uncertainty → accepted residual risk, not safe deletion comprobado |

---

## 4. Accepted Residual Risks

| Branch | Evidence Strength | Risk | Status |
|--------|------------------|------|--------|
| `codex/docs-skillhub-context-refresh-20260327` | MEDIUM-LOW | Possible loss of unique commits not verified against `batch-2d`. Redundancy was inferred, not proven. | **Accepted** — SHA `82862131` registered for potential recovery |
| `feat/skills-contracts-explain` | LOW-MEDIUM | Possible loss of LinterPlan / skill metadata contracts / `--explain` flag if never reintroduced in main. | **Accepted** — SHA `3e15a215` registered for potential recovery |
| `fix/search-context-preview-truncation` | HIGH | Low — PR #84 merged the functional fix. | **Accepted** — negligible residual risk |

---

## 5. Documents Modified

| File | Action | What Changed |
|------|--------|--------------|
| `hygiene/closed-pr-semantic-memo-20260509.md` | MODIFIED | Added evidence strength column, adjusted Rule 5, added accepted residual risk section, renumbered sections |
| `hygiene/README.md` | MODIFIED | Added duplicate warning about exported review bundles |
| `hygiene/phase-6-document-authority-fix-20260509.md` | MODIFIED | Clarified `stash-20260504.patch` status (deleted in Phase 3, not "still present") |
| `hygiene/git-hygiene-document-authority-20260509.md` | MODIFIED | Added correction report to authority registry, added authority map entry |
| `hygiene/closed-pr-semantic-memo-correction-20260509.md` | CREATED | This report |

---

## 6. Operational Changes

**None.** This is a documentation-only correction. No Git operations, no branch changes, no code changes.

---

## 7. Status

Corrección documental aplicada. No se revierten decisiones operacionales. Las ramas DELETED permanecen eliminadas. Las incertidumbres quedan clasificadas como accepted residual risk con evidencia strength calibrada.

---

*Generated as follow-up to `git-hygiene-closed-pr-semantic-memo` (engram #2750). Correction registered in authority registry.*
