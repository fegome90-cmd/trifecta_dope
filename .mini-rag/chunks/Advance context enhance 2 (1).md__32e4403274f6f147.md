### Atomic Writes and Locking

```python
# Atomic write pattern
with open(tmp_path, 'w') as f:
    json.dump(pack, f, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.rename(tmp_path, final_path)

# Lock file prevents concurrent builds
with filelock.FileLock("_ctx/.autopilot.lock"):
    build_context_pack(segment)
```
