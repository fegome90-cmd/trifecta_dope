## 3. Real Usage (Heuristic Subset)

We identified 39 events explicitly using `.` or relative paths (confirmed Real User CLI):

- **Commands**: `ctx.sync`, `ctx.get`, `ast.symbols`.
- **Success Rate**: 100%
- **Performance**:
  - `ast.symbols`: ~500ms (Cold start)
  - `ctx.sync`: ~500ms (Cold start)

*Note: Sample size (39) is small but confirms the sub-millisecond latency in global stats is indeed test noise.*

---
