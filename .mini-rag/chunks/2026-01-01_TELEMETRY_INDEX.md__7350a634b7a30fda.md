### Rule #3: Extend, Don't Duplicate
```python
# ✅ DO THIS:
telemetry.event("ctx.search", {...}, {...}, 100, bytes_read=1024)  # Extra field

# ❌ DON'T DO THIS:
# Don't create a second telemetry system or parallel log file
```
