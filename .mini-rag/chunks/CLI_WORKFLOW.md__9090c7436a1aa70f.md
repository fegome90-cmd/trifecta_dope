## Full Workflow Example (Copy/Paste)

```bash
# Step 1: Create segment
trifecta create -s /tmp/demo_segment

# Step 2: Sync (build + validate)
trifecta ctx sync -s /tmp/demo_segment

# Step 3: Search for context
trifecta ctx search -s /tmp/demo_segment -q "error handling"

# Step 4: Get specific chunks (use IDs from step 3 output)
trifecta ctx get -s /tmp/demo_segment -i prime-1,doc-error-3

# Step 5: Navigate code symbols (if Python files exist)
trifecta ast symbols "sym://python/mod/src.utils" --segment /tmp/demo_segment
```

---
