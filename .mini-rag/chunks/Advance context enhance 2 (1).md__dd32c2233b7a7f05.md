### Example: Baseline vs. Context Search

Before (loading 5 full files):

- Average context: ~8,000 tokens per turn
- Citation rate: 45% (agent rarely cites specific sections)
- Failures: Agent confuses information from different files

After (Context Search + Budget):

- Average context: ~2,500 tokens per turn
- Citation rate: 85% (clear `[chunk_id]` references)
- Failures: Agent explicitly states “no evidence found” when appropriate
