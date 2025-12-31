### 5. L2 Direct Trigger Matching

**New Method**: `_match_l2_nl_triggers(task, features) -> (feature_id, trigger)`

```python
def _match_l2_nl_triggers(self, task: str, features: dict):
    """L2: Direct NL trigger match (canonical intent phrases)."""
    nl_ngrams = self._normalize_nl(task)

    best_match = None
    best_trigger = None
    best_priority = 0

    for feature_id in sorted(features.keys()):  # Stable lexical order
        config = features[feature_id]
        nl_triggers = config.get("nl_triggers", [])
        priority = config.get("priority", 1)

        for trigger in nl_triggers:
            trigger_lower = trigger.lower().strip()

            # Exact match in normalized ngrams
            if trigger_lower in nl_ngrams:
                if priority > best_priority:
                    best_match = feature_id
                    best_trigger = trigger
                    best_priority = priority

    return best_match, best_trigger
```
