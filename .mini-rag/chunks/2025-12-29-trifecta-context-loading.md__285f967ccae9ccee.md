#### 4. **Atomic Write** (concurrency safety)

**De**: architecture-agent/resource-cleanup  
**Para Trifecta**: Lock + atomic write

```python
import fcntl

class AtomicWriter:
    def write(self, target: Path, content: str):
        """Write atomically with lock."""
        lock_file = target.parent / ".lock"
        
        with open(lock_file, 'w') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            
            try:
                # Write to temp
                temp = target.with_suffix('.tmp')
                temp.write_text(content)
                
                # Sync to disk
                with open(temp, 'r+') as f:
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                temp.rename(target)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
```

**ROI**: Alto si se corre desde hooks/CI.

---
