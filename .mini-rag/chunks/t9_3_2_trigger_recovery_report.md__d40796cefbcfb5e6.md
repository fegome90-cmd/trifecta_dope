### 7. plan_accuracy_top1 Metric

**File**: `src/infrastructure/cli.py` (eval-plan command)

**New Metric**:
```python
# Parse expected_feature_id from dataset
expected_features = {}
for line in content.split('\n'):
    match = re.match(r'^\d+\.\s+"([^"]+)"\s*\|\s*(\w+)', line)
    if match:
        task_str = match.group(1)
        expected_id = match.group(2)
        expected_features[task_str] = expected_id

# Track accuracy during evaluation
correct_predictions = 0
for task in tasks:
    result = use_case.execute(Path(segment), task)
    expected_id = expected_features.get(task)
    selected_id = result.get("selected_feature")

    if expected_id:
        if expected_id == "fallback":
            if selected_id is None:
                correct_predictions += 1
        elif selected_id == expected_id:
            correct_predictions += 1

plan_accuracy_top1 = (correct_predictions / expected_count * 100)
```

**Output**:
```
plan_accuracy_top1: 57.5% (23/40 correct)
```

---
