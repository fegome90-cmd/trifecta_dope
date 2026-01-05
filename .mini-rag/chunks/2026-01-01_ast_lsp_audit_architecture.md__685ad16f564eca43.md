## 5. Budget Policy (Bytes/Lines)

To protect the context window, the system MUST enforce strict **Byte/Line** limits. Tokens are for observation only.

| Limit Name | Safe Value | Action if Exceeded |
| :--- | :--- | :--- |
| `max_bytes_total_per_command` | **32,000 bytes** (~8k chars) | Return `BUDGET_EXCEEDED` error. |
| `max_snippet_bytes` | **2,000 bytes** | Truncate content, append comment `# ... truncated`. |
| `max_snippets_per_command` | **5** | Drop subequent results. |
| `max_lines_per_snippet` | **50 lines** | Truncate, append `# ... X lines hidden`. |

*Tokens*: MAY be calculated for telemetry (`telemetry.ast_tokens`), but MUST NOT determine logic flow.

---
