### What Would v1 Require?
1. **IPC Layer:**
   - Unix socket listener in daemon
   - Bridge: convert stdin/stdout ↔ socket I/O
   - PID file + heartbeat (prevent stale processes)

2. **Lifecycle Manager:**
   - Start daemon on segment init
   - Ensure running on every command
   - Kill on segment cleanup
   - Auto-restart if crashed

3. **Resource Limits:**
   - Max memory per daemon: 500MB
   - Max files kept open: 50
   - Idle timeout: 30min → shutdown

**Effort Estimate:** 3–4 days (after MVP stabilizes)

---
