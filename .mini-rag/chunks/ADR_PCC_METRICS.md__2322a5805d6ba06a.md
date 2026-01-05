### 2. True Zero Guidance (`true_zero_guidance_rate`)

**Definition:** Returns empty results (0 chunks, 0 paths, 0 next_steps) - a bug condition.

**Formula:**
```
true_zero_guidance = (chunks_count == 0 AND paths_count == 0 AND next_steps_count == 0)
```

**Guardrail:** `true_zero_guidance_rate` MUST be 0%.

**Rationale:** Empty results are never correct - they break workflows and indicate a bug in the planning logic.
