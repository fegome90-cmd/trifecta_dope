# ADR_T9_ROUTER_V1

## Scope
- Router v1 for `ctx.plan` (PCC-only, no RAG, no embeddings)

## Invariants
- Deterministic selection (stable ordering, no randomness)
- Tie -> fallback
- true_zero_guidance_rate = 0
- Bundle assertions: if bundle paths/anchors fail, degrade to fallback

## Matching Levels
- L1: Explicit feature id (`feature:<id>`) with fail-closed validation
- L2: Direct NL triggers (`nl_triggers`), scored and ranked
- L3: Alias triggers (`triggers`) with term counting
- L4: Fallback to PRIME entrypoints

## Scoring (L2)
- Exact match in ngrams: score = 2
- Subset match (all trigger terms present): score = 1
- Ranking order: score desc, specificity (word count) desc, priority desc

## Clamp (Single-Word)
- Applies when trigger word_count == 1 and feature priority >= 4
- Config-driven `support_terms` in `aliases.yaml`
- Allow only if query contains >= 1 support term
- Otherwise block with warning `weak_single_word_trigger`

## Warnings Taxonomy
- weak_single_word_trigger
- ambiguous_single_word_triggers
- match_tie_fallback
- bundle_assert_failed

## Gates
- Core Gate-NL
  - fallback_rate < 20%
  - true_zero_guidance_rate = 0%
  - alias_hit_rate <= 70%
- Quality Gate
  - plan_accuracy_top1 >= 75%
  - fallback_rate <= 15%
  - alias_hit_rate <= 40%

## Frozen for T10
- Router v1 behavior is frozen
- Any changes require ADR update + re-run gates
