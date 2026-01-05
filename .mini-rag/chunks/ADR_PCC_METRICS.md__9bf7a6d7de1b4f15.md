### 3. eval-plan Output

**Command:** `trifecta ctx eval-plan --segment <segment> --dataset <dataset>`

**Relevant Fields:**
- `selected_by`: Mechanism used (feature, nl_trigger, alias, fallback)
- `selected_feature`: Feature ID selected (if any)
- `paths`: List of file paths returned
- `chunk_ids`: List of chunk IDs returned

**Purpose:** Provides system predictions for comparison against ground truth.
