### ⚠️ Unsafe Uses (Lossy NOT OK)

- **Billing:** Cannot use for financial calculations (drops = missed charges)
- **Compliance Logs:** Cannot use for audit trails (drops = missing events)
- **Rate Limiting Gates:** Cannot use for quota enforcement (drops = bypass)
- **Distributed Locks:** Cannot use for coordination (drops = lost signals)

**Rule of Thumb:** If missing 1 event out of 100 breaks your use case, telemetry is the wrong tool.

---
