# Variant B Spec: Trifecta-aligned skill-hub pilot

## Goal
Evaluate whether a Trifecta-aligned retrieval policy improves coherence between user intent, query sent, skills recovered, and final selection.

## Non-goals
- No production replacement of `skill-hub`
- No parallel search engine
- No global architecture rewrite
- No extra retrieval intelligence beyond validity, guardrails, and traceability needed for the pilot

## Design rule
Variant B must remain a use case on top of Trifecta native capabilities.

## Retrieval contract
1. Input query is preserved for traceability.
2. Query may be normalized/reframed into an instruction-style query before retrieval.
3. Retrieval uses Trifecta search first.
4. Top candidates may be validated with Trifecta get/excerpt.
5. Final output is consolidated for decision support.
6. Retrieval evidence, confidence derivation, and presentation output must remain separately auditable.

## Frozen pilot inputs
- dataset: `data/skill_hub_pilot_queries.yaml` version 1
- corpus subset: `data/skill_hub_pilot_corpus_subset.yaml` version 1
- output schema: `docs/reports/skill_hub_ab_output_schema.md`
- reviewer protocol: `docs/reports/skill_hub_independent_reviewer_protocol.md`
- frozen skills-hub artifacts used by pilot must record hashes for:
  - `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`
  - `~/.trifecta/segments/skills-hub/_ctx/context_pack.json`
  - `~/.trifecta/segments/skills-hub/_ctx/aliases.yaml`
- baseline/runtime artifacts must record hashes for:
  - wrapper used to execute the arm
  - parser used to convert raw output to schema rows

## Explicit subset application mode
- Variant B retrieval runs against the full existing `~/.trifecta/segments/skills-hub` segment.
- The curated corpus subset is **not** a retrieval prefilter.
- The curated corpus subset is only an evaluation/audit lens for expected neighbors, duplicate behavior, and noise interpretation.

## B1. Query rewrite policy
Transform short or vague queries into instruction-shaped retrieval prompts.

### Rules
- If query is very short, vague, typo-prone, or abstract, rewrite to explicit task intent.
- Keep original language if possible.
- If ambiguity remains and query is Spanish, generate English fallback variant.
- Rewrites must be deterministic and logged.
- Rewrite may improve phrasing, but may not inject a synthetic winner unsupported by Trifecta retrieval.

### Example
Original:
- `optmizar procesos agenticos`

Rewrite candidate:
- `Encuentra skills para optimizar procesos agénticos, workflows multi-agente, coordinación operativa y planificación de ejecución`

Fallback English:
- `Find skills for optimizing agent workflows, multi-agent coordination, planning, and execution`

## B2. Search -> Get policy
### Pass 1
- Run Trifecta `ctx search` with rewritten instruction query.

### Pass 2
- If low-signal result set, run fallback search variant.

### Pass 3
- Run `ctx get --mode excerpt` on top-N candidates to validate semantic fit.

### N values
- Search top-N candidate pool: 5
- Excerpt validation set: 3

### Mandatory decision effect
If excerpt validation contradicts or materially weakens the current top1 recommendation, Variant B must do one of:
- change `recommended_skill`, or
- set `confidence=low`

Conflicting excerpt evidence cannot be reduced to a note while preserving a strong recommendation.

## B3. Fallback policy
Fallback triggers when one or more of the following happen:
- zero hits
- only one hit with low score
- top result appears semantically off-domain
- query language/typo ambiguity likely

Fallback actions:
- bilingual variant search
- explicit intent expansion
- alias-aware re-query if available

### Alias constraint
Aliases may support reformulation only. They may not become a dominant reranking layer that overrides Trifecta retrieval evidence.

## B4. Confidence policy (formal rubric)
Confidence must be driven by observable retrieval signals, not free-form narrative.

### Signals that raise confidence
- top1 is inside `expected_good_skills` or `acceptable_adjacent_skills`
- at least one expected good skill appears in top3
- top1 and top3 belong to the same intended domain cluster
- fallback was not needed, or fallback improved coherence materially
- excerpt validation supports the same domain/intention as top1 recommendation

### Signals that lower confidence
- zero hits
- single weak hit only
- top1 is outside expected domain
- no expected good skill in top3
- bilingual fallback still yields inconsistent domains
- excerpt validation conflicts with search ranking
- lexical trap / semantic-near-but-wrong query class
- negative-control query with contamination where evidence does not justify a single winner

### Mapping
- `high`: top1 useful = true AND top3 contains good candidate = true AND no severe false-positive signal
- `medium`: top1 useful = false but top3 contains good candidate = true, or top1 useful = true with conflicting/weak supporting signals
- `low`: no good candidate in top3, or severe false-positive signal, or negative-control query where system cannot justify a single winner safely

### Negative-control hardening
For negative controls, overclaiming with `medium` confidence is also considered severe when the query is obviously contaminated or structurally ambiguous and the system lacks sufficient evidence for a single winner.

## B5. Consolidation output format
Per query, Variant B should produce:
- original_query
- rewritten_query
- fallback_query_used (optional)
- search_results_top5
- excerpt_validated_top3
- recommended_skill
- alternatives
- confidence
- notes_on_false_positive_risk

Output must also conform to:
- `docs/reports/skill_hub_ab_output_schema.md`

## B6. No-regression rule
The following positive controls must not regress:
- `q04` how to implement test driven development with pytest fixtures
- `q07` security authentication review
- `q10` work order execution workflow

No-regression means:
- if baseline A has `top1_useful=true`, Variant B must preserve it
- otherwise Variant B must at least preserve `top3_contains_good_candidate=true`

## B7. Architectural guardrails
- No production wrapper changes in pilot
- No bypass of Trifecta engine
- No hardcoded giant if/else in CLI if policy can live in reusable spec/harness logic
- Retrieval and presentation remain separable
- No strong prefilter from manifest before `ctx search`
- No final recommendation based solely on manifest metadata or alias expansion

## B8. Required evidence per run
Every run must preserve:
- `runner_command`
- `wrapper_path`
- `wrapper_sha256`
- `parser_sha256`
- `run_started_at`
- `retrieval_raw_output_path`
- `presentation_output_path`
- frozen manifest/context/aliases hashes

If any frozen hash differs between A and B, the run is invalid and must abort before evaluation.
