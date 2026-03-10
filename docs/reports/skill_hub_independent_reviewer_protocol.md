# Skill Hub Independent Reviewer Protocol v1

## Goal
Provide a comparable review method for judging A/B pilot outputs with minimal hypothesis bias.

## Review mode
Preferred mode: **blind**.
Fallback mode: **semi-blind** if operational constraints require arm labels after scoring.

### Blind procedure
- Replace `arm` labels with neutral identifiers such as `X` and `Y` during scoring.
- Reviewer scores each row before seeing which arm is baseline or variant.
- Arm identity is revealed only after the per-query verdict sheet is frozen.

### Semi-blind procedure
- Reviewer may know that two arms exist but must not know which is baseline A or Variant B during initial scoring.
- If full blinding is impossible, record the reason explicitly in the review report.

## Inputs required
Reviewer must receive:
- per-query A/B rows conforming to `docs/reports/skill_hub_ab_output_schema.md`
- dataset file `data/skill_hub_pilot_queries.yaml`
- raw retrieval outputs for each row
- presentation outputs for each row
- frozen hashes and run metadata

Reviewer should not need extra repo discovery.

## Scoring principles
### 1. Evaluate evidence before narrative
Judge first from:
- original query
- search query used
- top1/top3
- confidence
- confidence reason codes
- raw retrieval output
- excerpt evidence if present

Do not give credit merely for polished presentation.

### 2. Cross-source duplicates
When the same skill appears from multiple sources:
- treat same-name cross-source duplicates as the same semantic skill unless source differences materially change meaning
- do not penalize an arm for choosing the canonical duplicate if the recommendation is otherwise coherent
- do penalize if duplicate noise creates unjustified confidence or hides a stronger same-domain alternative

### 3. Acceptable adjacent skills
If the dataset row includes `acceptable_adjacent_skills`:
- treat those as valid same-domain alternatives for `top1_useful` / `top3_contains_good_candidate`
- do not automatically treat adjacent skills as equal to exact expected skills for confidence; confidence still depends on evidence quality
- do not use acceptable-adjacent logic to rescue a negative control or to bypass a no-regression failure on frozen positive controls

If a recommendation is same-domain and clearly reasonable but not listed:
- reviewer may mark `adjacent_reasonable_unlisted=true` in notes
- reviewer should not silently upgrade the score; must explain why

### 4. No sufficient evidence
Use `no sufficient evidence` when:
- query is structurally ambiguous or contaminated
- top candidates span conflicting domains
- raw retrieval is weak, sparse, or unstable
- excerpt evidence conflicts with the chosen winner
- confidence reason codes do not show enough support for a single winner

Operational reading:
- `sufficient evidence` normally requires aligned retrieval signals for one domain, no decisive excerpt conflict, and confidence reason codes consistent with the recommendation
- if those conditions are absent, the reviewer should default to `no sufficient evidence`

In these cases, low confidence is usually correct.
Medium or high confidence requires explicit evidence.

### 5. Negative-control strictness
For negative controls:
- prefer caution over forced selection
- a single winner with `high` confidence is severe false positive unless evidence is unusually clean
- a single winner with `medium` confidence is also severe false positive if the query is contaminated or insufficiently grounded
- ambiguous alternatives may be listed, but only with explicit insufficiency notes

### 6. Hard-positive strictness
For hard-positives:
- failure to produce any expected or acceptable adjacent candidate in top3 is serious
- low confidence is acceptable only if raw evidence is genuinely weak
- repeated low-confidence behavior on hard-positives should be treated as benchmark weakness even if negatives are handled cautiously

## Verdict format per review batch
Reviewer must produce, at minimum:
- what was reviewed
- per-slice verdicts (`hard-positive`, `ambiguous`, `negative`)
- overall verdict
- top findings
- any invalidating issue
- whether A/B remained comparable

## Comparable verdict labels
Use one of:
- `pass`
- `pass with issues`
- `fail`
- `invalid run`

## Frozen decision hierarchy
The reviewer must apply this order strictly:
1. `invalid run`
2. `no_regression_positive_controls` failure
3. severe false positive on negative controls, including medium-confidence overclaim without sufficient evidence
4. slice failure on `hard-positive`, `ambiguous`, or `negative`
5. overall thresholds

Lower-priority success cannot override higher-priority failure.

## Invalid run criteria
Mark the batch `invalid run` if any of these occur:
- frozen hashes differ between A and B without declared experiment bump
- raw retrieval outputs are missing
- presentation outputs are missing
- parser/wrapper evidence is missing
- arm comparison is materially confounded by missing evidence
- arm improvement appears attributable to post-processing only and cannot be disentangled

## Verdict meaning
- `pass`: no invalid-run condition, no no-regression failure, no review-blocking severe false positive, no slice failure, and overall thresholds met
- `pass with issues`: no invalid-run condition, no no-regression failure, no review-blocking severe false positive, no slice failure, but minor documentation/interpretation issues remain
- `fail`: any failure in hierarchy items 2-4, even if overall thresholds pass
- `invalid run`: hierarchy item 1 triggered

## Minimal per-query note template
- Query ID:
- Arm judged better:
- Why:
- Confidence appropriate?:
- Severe false positive?:
- Adjacent acceptable used?:
- No sufficient evidence?:
- Comparability concern?:

## Output requirement
The reviewer report must be standalone and comparable across reruns.
