### 1. Path Correctness (`path_correct`)

**Definition:** The predicted feature matches the expected feature AND at least one predicted path is in the expected paths list from PRIME `index.feature_map`.

**Formula:**
```
path_correct = (
    expected_feature != "fallback" AND
    predicted_feature == expected_feature AND
    any(predicted_path in expected_paths)
)
```

**Rationale:** Path correctness is critical for tool-calling. Selecting the right feature but pointing to the wrong files results in broken context and failed operations.
