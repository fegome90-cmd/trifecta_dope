# Phase 6.5 — Metadoc hygiene proposal for `skill-hub`

## Scope
This document covers only Ola 1 hygiene decisions for non-skill documents that contaminate the main search surface.

Target metadocs:
- `prime_skills-hub.md`
- `agent_skills-hub.md`
- `session_skills-hub.md`
- `AGENTS.md`
- `README.md`

## Evidence base
Observed contamination in Phase 6:
- `q02` top hits: `prime_skills-hub`, `agent_skills-hub`
- `q12` top hits: `AGENTS.md`
- `context_pack.json` confirms these files are in the indexable source set

## Decision table

| File | Observed contamination | Decision | Why |
|---|---|---|---|
| `prime_skills-hub.md` | yes (`q02`) | exclude from main skill search surface | It is a hub explainer/reading list, not an executable skill. It absorbs generic “skill” queries. |
| `agent_skills-hub.md` | yes (`q02`) | exclude from main skill search surface | It is index/config metadata, not a user-facing operational skill. |
| `session_skills-hub.md` | indirect risk | exclude from main skill search surface | Session notes are history, not task skills. They are especially risky for vague queries. |
| `AGENTS.md` | yes (`q12`) | exclude from main skill search surface | It is governance/operational guidance for agents, not a skill entry. |
| `README.md` | indirect risk | exclude from main skill search surface | It is onboarding/reference documentation for the segment, not an executable skill. |

## Why exclusion beats degradation here
These files are not just noisy duplicates. They belong to a different document class:
- inventory docs
- hub docs
- governance docs
- session/history docs

Degrading them still leaves them in the competition set for abstract queries. Since the problem is class mismatch, exclusion is cleaner than soft demotion.

## What not to do in Ola 1
- do not edit Trifecta ranking logic
- do not add a reranker
- do not compensate from the harness
- do not rewrite user queries more aggressively
- do not touch aliases yet

## Minimal implementation options
Compatible with the current pattern:
1. remove these files from the segment's searchable source set when building/searching the skill surface
2. if hard exclusion is operationally difficult, move them to a non-primary documentation-only area outside the searchable skill corpus
3. only if neither is possible, tag them in metadata as non-skill docs and exclude them from the skill search feed that powers `skill-hub`

## Recommended action for Ola 1
Recommended immediate action:
- **exclude all five metadocs from the main skill search surface**

Rationale:
- strongest evidence of contamination
- smallest change with clearest causal signal
- cleanest E1 experiment design (`q02`, `q12`, controls `q07`, `q10`)

## Status
**pass**
