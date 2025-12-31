### Backpressure prevents runaway requests

If the agent requests too much, the runtime:

- Returns what fits within budget
- Forces the agent to refine its query
- Enforces a maximum of rounds per turn (e.g., 1 search + 1 get)

This prevents loops and keeps costs predictable.
