# Skills Trigger Collision Report

## Executive summary

- Skills analyzed: 72
- Collision candidates: 76
- High severity: 0
- Medium severity: 0
- Low severity: 76

## Threshold calibration

| Severity | Threshold | Description |
|----------|-----------|-------------|
| HIGH     | >= 0.44   | Intervention required |
| MEDIUM   | >= 0.35   | Review recommended |
| LOW      | >= 0.18   | Expected noise, acceptable |

**Note:** Collisions with MEDIUM score < 0.40 are generally unavoidable when skills share domain vocabulary (e.g., 'claude', 'code', 'sessions' in AI-related skills).

## Family distribution

- `meta-pi-trifecta`: 20
- `search-exploration-retrieval`: 13
- `frontend-design-ui`: 10
- `docs-formats`: 8
- `review-security-verification-debug`: 7
- `backend-python-testing-standards`: 6
- `other`: 4
- `git-pr-workflow`: 3
- `ai-rag-data-db`: 1

## Top collision candidates

- `qwen3-tts` vs `quick-setup` — severity=low, score=0.30, raw=0.30, penalty=0.00, overlap=generate, setup
  - rationale: same family, same artifact focus, same workflow phase, 2 shared trigger terms, raw=0.30, final=0.30
- `codebase-explorer` vs `trifecta-graph-explorer` — severity=low, score=0.30, raw=0.34, penalty=0.04, overlap=code, explain, explorer
  - rationale: same family, same artifact focus, same workflow phase, 3 shared trigger terms, raw=0.34, boundary_penalty=0.04, primary intent differs, final=0.30
- `sqlite-ops` vs `postgres-patterns` — severity=low, score=0.30, raw=0.34, penalty=0.04, overlap=database, patterns, schema
  - rationale: same family, same artifact focus, 3 shared trigger terms, raw=0.34, boundary_penalty=0.04, primary intent differs, final=0.30
- `gdcli` vs `gmcli` — severity=low, score=0.30, raw=0.30, penalty=0.00, overlap=cli, searching
  - rationale: same family, same workflow phase, 2 shared trigger terms, raw=0.30, final=0.30
- `skill-creator` vs `tdd-workflow` — severity=low, score=0.29, raw=0.29, penalty=0.00, overlap=skill, test
  - rationale: same family, same artifact focus, same workflow phase, 2 shared trigger terms, raw=0.29, final=0.29
- `backend-implementation-patterns` vs `learned-progressive-disclosure` — severity=low, score=0.28, raw=0.28, penalty=0.00, overlap=skill
  - rationale: same family, same artifact focus, same workflow phase, 1 shared trigger terms, raw=0.28, final=0.28
- `docx` vs `theme-factory` — severity=low, score=0.27, raw=0.27, penalty=0.00, overlap=artifact
  - rationale: same family, same artifact focus, same workflow phase, 1 shared trigger terms, raw=0.27, final=0.27
- `coding-standards` vs `java-coding-standards` — severity=low, score=0.26, raw=0.26, penalty=0.00, overlap=coding, immutability, naming, project, standards
  - rationale: same artifact focus, 5 shared trigger terms, raw=0.26, final=0.26
- `project-guidelines-example` vs `quick-setup` — severity=low, score=0.26, raw=0.30, penalty=0.04, overlap=project
  - rationale: same family, same artifact focus, same workflow phase, 1 shared trigger terms, raw=0.30, boundary_penalty=0.04, primary intent differs, final=0.26
- `frontend-patterns` vs `python-patterns` — severity=low, score=0.26, raw=0.26, penalty=0.00, overlap=code, patterns, skill
  - rationale: same artifact focus, same workflow phase, 3 shared trigger terms, raw=0.26, final=0.26
- `find-skills` vs `continuous-learning` — severity=low, score=0.26, raw=0.26, penalty=0.00, overlap=skills
  - rationale: same family, same artifact focus, 1 shared trigger terms, raw=0.26, final=0.26
- `continuous-learning` vs `learned-progressive-disclosure` — severity=low, score=0.26, raw=0.26, penalty=0.00, overlap=learned, skills
  - rationale: same family, same artifact focus, 2 shared trigger terms, raw=0.26, final=0.26
- `checkpoint-card` vs `continuous-learning` — severity=low, score=0.25, raw=0.25, penalty=0.00, overlap=save, session
  - rationale: same family, same artifact focus, 2 shared trigger terms, raw=0.25, final=0.25
- `find-skills` vs `indexing-skills-safely` — severity=low, score=0.25, raw=0.25, penalty=0.00, overlap=skill, skills
  - rationale: same family, same artifact focus, 2 shared trigger terms, raw=0.25, final=0.25
- `vercel-react-native-skills` vs `skill-creator` — severity=low, score=0.25, raw=0.25, penalty=0.00, overlap=performance, skills
  - rationale: same family, same artifact focus, 2 shared trigger terms, raw=0.25, final=0.25
- `learned-progressive-disclosure` vs `project-guidelines-example` — severity=low, score=0.25, raw=0.29, penalty=0.04, overlap=skills
  - rationale: same family, same artifact focus, same workflow phase, 1 shared trigger terms, raw=0.29, boundary_penalty=0.04, primary intent differs, final=0.25
- `python-cli-patterns` vs `continuous-learning` — severity=low, score=0.24, raw=0.24, penalty=0.00, overlap=patterns
  - rationale: same family, same artifact focus, 1 shared trigger terms, raw=0.24, final=0.24
- `continuous-learning` vs `project-guidelines-example` — severity=low, score=0.24, raw=0.24, penalty=0.00, overlap=skills
  - rationale: same family, same artifact focus, 1 shared trigger terms, raw=0.24, final=0.24
- `indexing-skills-safely` vs `project-guidelines-example` — severity=low, score=0.24, raw=0.24, penalty=0.00, overlap=skills
  - rationale: same family, same artifact focus, 1 shared trigger terms, raw=0.24, final=0.24
- `brand-guidelines` vs `project-guidelines-example` — severity=low, score=0.24, raw=0.24, penalty=0.00, overlap=guidelines
  - rationale: same family, same artifact focus, 1 shared trigger terms, raw=0.24, final=0.24

## Prioritized intervention backlog

### L1-review-security-verification-debug

- skills: `security-review`, `debug-helper`, `verification-loop`, `learned-pr-feedback-resolution`, `branch-review-api`
- why now: High confusion risk in quality, review, security, and failure-analysis prompts.
- collisions in lot: 1
- high severity in lot: 0
- top cases:
  `learned-pr-feedback-resolution` vs `security-review` — severity=low, score=0.19, raw=0.28, penalty=0.09, overlap=review, security, skill

### L2-search-exploration-retrieval

- skills: `cli-explorer`, `codebase-explorer`, `rctl-explore`, `web-search`, `web-fetch`, `brave-search`, `context7`
- why now: Discovery tasks can route to the wrong search surface or wrong depth of analysis.
- collisions in lot: 1
- high severity in lot: 0
- top cases:
  `cli-explorer` vs `web-search` — severity=low, score=0.20, raw=0.29, penalty=0.09, overlap=lightweight, prefer, quick, search

### L3-backend-python-testing

- skills: `backend-implementation-patterns`, `python-patterns`, `python-testing`, `tdd-workflow`, `coding-standards`, `python-cli-patterns`
- why now: Implementation and language/testing guidance overlap on common developer prompts.
- collisions in lot: 0
- high severity in lot: 0
- top cases: none detected by current heuristic

### L4-docs-formats

- skills: `docx`, `pptx`, `xlsx`, `doc-coauthoring`, `nutrient-document-processing`, `internal-comms`
- why now: Document intent often overlaps with file-format-specific execution skills.
- collisions in lot: 1
- high severity in lot: 0
- top cases:
  `docx` vs `nutrient-document-processing` — severity=low, score=0.21, raw=0.47, penalty=0.26, overlap=api, cross, document, documents, docx, format

### L5-frontend-design-ui

- skills: `frontend-patterns`, `frontend-design`, `web-design-guidelines`, `vercel-react-best-practices`, `vercel-composition-patterns`
- why now: Frontend implementation, design, and UI review often share vocabulary but require distinct execution.
- collisions in lot: 0
- high severity in lot: 0
- top cases: none detected by current heuristic

## Heuristic notes

- Collision score is now boundary-aware: raw lexical overlap is reduced by explicit fences such as `Do NOT use`, `Prefer this over`, artifact specialization, and workflow-phase specialization.
- `boundary_strength` in the enriched CSV is a per-skill hint for how strongly that skill declares its own frontier.
- This report is for prioritization only; it does not modify any `SKILL.md` file.
- False positives remain possible, especially for broad generic skills or skills that mention siblings without an explicit fence.