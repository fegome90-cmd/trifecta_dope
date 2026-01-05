### 2. False Fallback (`false_fallback`)

**Definition:** The system selected fallback mode when a feature-based selection was expected (i.e., expected_feature != "fallback" and selected_by == "fallback").

**Formula:**
```
false_fallback = (expected_feature != "fallback" AND selected_by == "fallback")
```

**Rationale:** False fallbacks indicate the system failed to match a known feature when it should have. This is a quality regression - we fell back to generic context when specific context was available.
