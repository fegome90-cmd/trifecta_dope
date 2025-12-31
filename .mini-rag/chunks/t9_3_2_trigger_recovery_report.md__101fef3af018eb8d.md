### 3. 4-Level Priority Hierarchy Implementation

**File**: `src/application/plan_use_case.py`

**New Hierarchy**:
```
L1: Explicit feature:<id> (highest priority)
    ↓
L2: Direct NL trigger match (NEW - canonical intent phrases)
    ↓
L3: Alias match (structured triggers with term counting)
    ↓
L4: Fallback to entrypoints (lowest priority)
```

**Key Changes**:
- Added `_normalize_nl()` method with bigram generation
- Added `_match_l2_nl_triggers()` for direct phrase matching
- Renamed `_match_l2_alias()` → `_match_l3_alias()`
- Updated `execute()` to use 4-level cascade
