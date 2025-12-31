### 2. Improved L2 Matching Logic with Scoring

**File**: `src/application/plan_use_case.py`

**New Scoring System**:
```python
def _match_l2_nl_triggers(task, features) -> (feature_id, trigger, warning, score, match_mode):
    """
    Scoring (T9.3.3):
    - score=2: Exact phrase match in ngrams
    - score=1: All trigger words present (subset match)
    - score=0: No match

    Single-word guardrail:
    - Only allowed if priority >= 4
    - AND no conflicts with other single-word triggers
    - Conflict → fallback with warning

    Tie handling:
    - Tie in (score, priority) → fallback with warning
    """
```

**Key Implementation Details**:
- Track all candidates with scores
- Filter by single-word guardrail (priority >= 4)
- Detect conflicts between single-word triggers from different features
- Sort by (score desc, priority desc) and check for ties
