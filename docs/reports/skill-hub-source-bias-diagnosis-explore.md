# skill-hub-source-bias-diagnosis — sdd-explore

status: explored
executive_summary: Skill-hub search and cards are currently governed by the promoted skill_hub set in `~/.trifecta/segments/skills-hub/_ctx` (manifest + context pack + promotion receipt). The observed source mix is mostly upstream data, not a segment/default-path bug: the live manifest is overwhelmingly `pi-agent-skills`-backed (171 of 172 entries, with only 1 `codex-skills` entry), and cards render `Source` from chunk text first, then path inference. Export/catalog data is a separate surface and does not appear to be the runtime authority.
artifacts:
  engram: skill-hub/source-authority
  filesystem: docs/reports/skill-hub-source-bias-diagnosis-explore.md
next_recommended: Validate whether the source skew users see is acceptable product behavior or whether the manifest should be rebalanced/partitioned; if fixing, choose between (1) adjusting manifest contents, (2) changing search result ranking/surface labeling, or (3) splitting runtime source groups into separate promoted sets.
risks: The current data makes mixed-source results plausible even when the runtime is correct, so a UX-only fix could mask an upstream curation issue. The cards renderer will continue to prefer chunk-embedded Source metadata, so any new canonical source policy must be enforced at generation time, not by docs.
skill_resolution: injected

## Exploration Notes
- `scripts/skill-hub` searches the default promoted segment `~/.trifecta/segments/skills-hub` unless `SKILL_HUB_SEGMENT` is set.
- `ContextService` loads the promoted set via `_ctx/skills_manifest.json`, `_ctx/context_pack.json`, and `_ctx/skill_hub_promotion_receipt.json`, verifying fingerprints before use.
- `skill_hub_cards_core.py` promotes search hits only when it can trust `read` path, `# Skill:` title, `Source`, and description fields; `Source` comes from chunk content before path inference.
- `data/skills_catalog/skills_catalog.csv` is an offline export and not runtime authority for skill-hub search/cards.

## Evidence
- Manifest counts: `pi-agent-skills` = 171, `codex-skills` = 1.
- `security`, `openai-docs` return pi-agent-skills-heavy results because the live manifest is pi-agent-skills-heavy.
- `codex` returns a mixed surface because the catalog contains both codex and pi-agent adjacent skills, but the runtime still resolves against the promoted set.
