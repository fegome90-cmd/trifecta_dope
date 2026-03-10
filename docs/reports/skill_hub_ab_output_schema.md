# Skill Hub Pilot A/B Output Schema v1

Each query result row must contain:
- query_id
- original_query
- control_type
- difficulty
- arm (`A` or `B`)
- dataset_version
- corpus_subset_version
- manifest_sha256
- context_pack_sha256
- aliases_sha256
- wrapper_path
- wrapper_sha256
- parser_sha256
- runner_command
- run_started_at
- search_query_used
- fallback_query_used (nullable)
- retrieval_raw_output_path
- presentation_output_path
- top1_name
- top1_source
- top1_score_raw
- top3_names
- recommended_skill
- alternatives
- confidence
- confidence_reason_codes
- severe_false_positive
- top1_useful
- top3_contains_good_candidate
- confidence_matches_reality
- notes

## Comparability rules
- Same dataset version across A/B
- Same corpus subset version across A/B
- Same frozen artifact hashes across A/B unless the experiment explicitly states otherwise
- Same wrapper path/hash and parser hash across repeated runs of the same arm unless a new experiment version is declared
- Same evaluation rubric across A/B
- All metric judgments recorded per query
- Retrieval raw output and presentation output must be preserved separately for each arm/query
- Abort before B if any of these differ from frozen A without explicit experiment-version bump:
  - dataset_version
  - corpus_subset_version
  - manifest_sha256
  - context_pack_sha256
  - aliases_sha256
  - wrapper_sha256
  - parser_sha256

## Layer evidence rules
- `retrieval_raw_output_path` must point to the unnormalized raw command output used to derive ranking evidence.
- `presentation_output_path` must point to the human-facing consolidated output for that row.
- `confidence_reason_codes` must contain machine-readable reasons such as `top3_match`, `excerpt_conflict`, `fallback_used`, `negative_control`, `low_signal`, `adjacent_match`.

## Evaluation notes
- For negative controls, `severe_false_positive=true` when the system overclaims a single winner with high confidence, or with medium confidence despite insufficient evidence.
- `acceptable_adjacent_skills` may be used by the reviewer protocol to avoid penalizing clearly reasonable same-domain recommendations.
