---
title: Skill Hub Manual
status: final
updated: 2026-03-13
scope: diagnostic-and-experimental-mission
owner: agent-runtime
---

# Skill Hub — Manual Operativo

## Table of Contents

- [1. Decision](#1-decision)
- [2. Purpose](#2-purpose)
- [3. North Star and Constraints](#3-north-star-and-constraints)
- [4. What Was Built Methodologically](#4-what-was-built-methodologically)
- [5. Experimental Record](#5-experimental-record)
- [6. Branch Outcomes](#6-branch-outcomes)
  - [6.1 q01](#61-q01)
  - [6.2 q09](#62-q09)
  - [6.3 q02](#63-q02)
  - [6.4 q12](#64-q12)
- [7. Cross-Branch Learnings](#7-cross-branch-learnings)
- [8. Rules for Future Skill Hub Work](#8-rules-for-future-skill-hub-work)
- [9. Outcome](#9-outcome)

---

## 1. Decision

**Current mission status:** `CLOSED`

**Final branch states:**
- `q09 = CLOSED`
- `q02 = STOP TEMPORAL`
- `q12 = STOP TEMPORAL`

**Operational decision:**
This mission does **not** justify further local skill curation, further patching of target skills, or broader reruns inside the same frame.

---

## 2. Purpose

Skill Hub exists to retrieve the most useful skill from a global skill library on the machine, using the normal Trifecta segment flow.

The mission objective was **not** to build a new search engine or replace Trifecta, but to improve **useful skill discoverability** inside the existing retrieval framework.

---

## 3. North Star and Constraints

These constraints remained mandatory throughout the mission:

- do not modify Trifecta
- do not create a parallel system
- do not introduce new infrastructure
- do not jump prematurely to SQLite, a new index, or a formal catalog
- do not touch production
- do not “solve” the issue via an external dominant harness/parser workaround
- prefer incremental corpus/metadata curation before adding intelligence
- preserve experimental discipline:
  - clean baseline
  - bounded changes
  - real comparability
  - no mixed mechanisms
  - explicit branch closure when a branch stops belonging to the mission

---

## 4. What Was Built Methodologically

### 4.1 Clean Baseline and Canonical Rerun

A materially better experimental base was established:

- frozen dataset
- frozen harness/parser
- fixed query scope
- preflight
- integrity checks
- comparable runs
- traceable artifacts linked to the canonical rerun

### 4.2 Evaluation Rule That Survives This Mission

A run only counts if:

- the run is comparable
- the change is bounded
- the controls do not degrade
- the result answers the real objective
- the primary evidence is anchored to the canonical baseline

### 4.3 Process Rule Learned

A phase must not silently turn from design into execution.

Even if a non-destructive execution yields useful signal, that must **not** be normalized as the default process.

---

## 5. Experimental Record

### 5.1 Alias Wave

Aliases were evaluated as the first clean lever.

**Result:** did not produce a defensible improvement path.

**Learning:** aliases alone did not resolve the hard cases.

### 5.2 Wave 1 — Minimal Visible Naming

Titles and a short visible line were adjusted on target skills.

**Result:** fail as intervention.

No material improvement on the focus set:
- `q01`
- `q02`
- `q09`
- `q12`

**Learning:** visible naming alone was insufficient.

### 5.3 Wave 2 — Minimal Discriminative Content

Short lines such as:
- `Intent`
- `Use when`
- `Do not use when`

were added or adjusted on core skills.

**Result:** fail as intervention.

**Learning:** brief local skill curation also did not move the hard cases.

### 5.4 Pivot to Retrieval Competition

After local curation failed, the mission pivoted from “fix the target skill” to:

- what is winning above it
- what surfaces are competing
- whether the target is absent or drowned out
- whether the query is captured by meta/neighbor surfaces first

**Result:** this pivot paid off.

**Core learning:** the failure modes were **not uniform**.

---

## 6. Branch Outcomes

### 6.1 q01

### Decision

`q01` was not treated as the same mechanism as `q02/q09/q12`.

### Evidence

`q01` behaved as a **present in A / lost in B** case:
- targets appeared in the rawer retrieval side
- but did not survive the later effective surface

### Outcome

This was not a “target missing from corpus” case.
It established that at least one branch was about **survival under the downstream surface**, not absence.

---

### 6.2 q09

### Decision

`q09 = CLOSED`

No further target-side local patching is justified inside this mission.

### Evidence

Audit showed that:
- `learned-pr-feedback-resolution` was indexed
- `branch-review-api` was indexed
- both had real retrieval-facing surfaces
- both could appear in other contexts

Exploratory and confirmatory query-form screens then showed a stable lexical split:

**Target enters with:**
- `PR feedback`
- `feedback de PR`

**Target does not enter with:**
- `review comments`
- `comentarios de review`

### Outcome

`q09` stopped being a local skill-representation problem.
It became much closer to a **query-form / phrasing sensitivity** issue.

That means it no longer belongs to local skill curation in this mission.

---

### 6.3 q02

### Decision

`q02 = STOP TEMPORAL`

### Evidence

`q02` showed strong prior capture from surfaces such as:
- plugin/package entries
- neighbor docs
- orthogonal skills
- administrative/meta surfaces

A first minimal experimental filter removed only:
- plugin/package surfaces
- docs/metadocs neighbors

and intentionally kept:
- orthogonal skills

After that filter, no comparably useful operational window emerged.

### Outcome

`q02` did not justify continued work in parallel with `q12`.
Continuing would have required more interpretive exclusions, not disciplined local filtering.

---

### 6.4 q12

### Decision

`q12 = STOP TEMPORAL`

### Evidence

`q12` also showed prior capture, but unlike `q02`, it responded usefully to the first minimal filter.

After removing clear meta/neighbor capture, the surviving top window included:
1. `dispatching-parallel-agents`
2. `examen-task-status`
3. `examen-finishing-a-development-branch`
4. `examen-test-driven-development`
5. `examen-subagent-driven-development`

That allowed a real pairwise competition analysis between:
- `dispatching-parallel-agents`
- `examen-subagent-driven-development`

What the comparison showed:
- `dispatching-parallel-agents` aligns strongly with the `multiple agents` axis
- but its own visible surface explicitly limits use for:
  - shared-plan coordination
  - work orchestration
- `examen-subagent-driven-development` aligns more with:
  - development task
  - implementation plan
  - execution with independent tasks in-session

### Outcome

The remaining conflict in `q12` was no longer gross meta-capture.
It became an **intent ambiguity** inside the query itself:

- parallelize independent subtasks
- or coordinate/orchestrate multiple agents in a stronger sense

A second fine-grained filter would have required assuming one reading of `coordinate`, and that interpretation was **not certified by the query**.

So the branch stopped here.

---

## 7. Cross-Branch Learnings

### 7.1 There Was No Single Mechanism

This mission’s most important finding:

The hard failures did **not** reduce to one shared explanation.

At least three distinct mechanisms appeared:
- target present but not surviving downstream (`q01`)
- sensitivity to query form / lexical family (`q09`)
- prior capture followed by residual intent ambiguity (`q12`)

`q02` additionally showed that not every prior-capture case unlocks in the same way.

### 7.2 What Actually Improved

The mission materially improved:
- diagnostic precision
- baseline quality
- traceability discipline
- separation of primary evidence from historical corroboration
- branch governance
- ability to close lines of work honestly

### 7.3 What Did Not Materially Improve

The mission did **not** produce a clear, stable improvement in useful retrieval for the hardest cases.

In practical terms:
- no small local lever was validated as the main fix
- no bounded local intervention proved worthy of promotion
- no stable recovery improvement was established for `q01/q02/q09/q12`

**Honest balance:**
The mission substantially improved system understanding.
It did **not** yet materially improve difficult-case retrieval.

---

## 8. Rules for Future Skill Hub Work

### 8.1 What Must Not Be Done Again Under This Mission Frame

Do not:
- reopen `q09` as local skill curation
- mix `q09` with `q02/q12`
- treat `q02` and `q12` as one block again
- patch local skills based on intuition
- keep filtering once the problem has moved from prior capture to intent ambiguity
- jump to:
  - SQLite
  - catalog
  - new index
  - parallel architecture
  without a new explicit mission

### 8.2 What Must Not Be Sold as Success

Do not confuse:
- **better diagnosis** with **better product**
- **useful screen** with **causal proof**
- **observable correlate** with **demonstrated cause**
- **noise suppression** with **problem solved**
- **candidate emergence** with **correct answer validated**
- **useful accidental result** with **disciplined process**

### 8.3 What Would Be Legitimate as Separate Future Missions

#### Future branch for q09
**Query-side sensitivity / phrasing sensitivity**

#### Future branch for q12
**Intent ambiguity / disambiguation**

#### Future branch for q02
Only if a new hypothesis appears that is better than:
- “keep filtering”
- “keep patching”

### 8.4 Governance Rule

When a branch moves from:
- a clear local corpus problem

to:
- query sensitivity
- intent ambiguity
- interpretive competition between plausible candidates

that branch no longer belongs to local Skill Hub curation and must either:
- close
- or reopen as a new mission with a different object

---

## 9. Outcome

### Mission board

- `q09 = CLOSED`
- `q02 = STOP TEMPORAL`
- `q12 = STOP TEMPORAL`
- `skill-hub current mission = CLOSED`

### Final executive summary

Skill Hub did not yet improve clearly on useful retrieval for the hardest cases.

But the mission produced something valuable and durable:
- it ruled out micro-local curation as the main line
- it exposed retrieval competition and prior capture
- it separated mechanisms instead of forcing a single story
- it closed branches with discipline
- it avoided building a premature solution on top of a mixed diagnosis

That is not a product win.
But it **is** a real improvement in judgment quality.
