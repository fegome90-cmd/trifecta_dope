# Dependabot Policy — Final Authority Correction

> **Date**: 2026-05-09
> **Purpose**: Scope correction reports as historical evidence and clarify final authority.
> **Status**: AUTHORITATIVE — correction of document scope, not policy content.

---

## Problem Detected

Two correction reports (`dependabot-policy-correction-20260509.md` and `dependabot-policy-semver-correction-20260509.md`) were marked with "Full document" authority scope in the authority registry. This creates a contradiction: these earlier correction reports can be cited as final authority even where they are superseded by later corrections and the updated policy document.

Additionally, Section 5.4 of `dependabot-policy-20260509.md` contained a contradictory phrase: "0.x minors are ALSO individual PRs (ignored by Dependabot, require SDD)". If Dependabot ignores them, they are NOT Dependabot PRs — they are handled entirely outside the normal Dependabot flow.

---

## Documents Adjusted

### 1. Authority Registry (`git-hygiene-document-authority-20260509.md`)

**Change**: Scope of `dependabot-policy-correction-20260509.md` and `dependabot-policy-semver-correction-20260509.md` updated from "Full document" to:

> Historical correction report; superseded where contradicted by `dependabot-policy-high-patch-only-correction-20260509.md` and current `dependabot-policy-20260509.md`.

**Rationale**: These correction reports are chronological evidence of the policy evolution. They should not override the latest correction or the updated policy where contradictions exist.

### 2. Policy Document (`dependabot-policy-20260509.md`)

**Change**: Section 5.4, bullet "0.x minors" — replaced:

- BEFORE: "For HIGH 0.x packages, semver-minor updates are ALSO individual PRs (ignored by Dependabot, require SDD)"
- AFTER: "0.x minors for HIGH packages are ignored by Dependabot and must be handled outside the normal Dependabot flow through SDD/manual review."

**Rationale**: Ignored packages do not generate Dependabot PRs. The word "ALSO" implied they somehow coexist as PRs — they do not. They are handled entirely outside Dependabot.

### 3. README (`hygiene/README.md`)

**Change**: Added authority clarification note above the Open Follow-ups section:

> Dependabot correction reports are chronological evidence. The final policy authority is `dependabot-policy-20260509.md` plus the latest `dependabot-policy-high-patch-only-correction-20260509.md`.

---

## Confirmation

- [x] The final policy maintains **HIGH = patch-only** for all HIGH packages (both 0.x and stable).
- [x] `.github/dependabot.yml` was **NOT modified** in this correction.
- [x] No functional code was touched.
- [x] No branches, tags, or dependencies were changed.

---

## Recommendation

**Ready for apply after human approval.** The policy document and all correction reports are now consistent. No further documentation corrections are needed before the operational apply of `.github/dependabot.yml`.

---

*Generated: 2026-05-09 | Status: AUTHORITATIVE | Change: dependabot-policy-final-authority-correction | No operational changes.*
