### Why Not in v0?
1. **No IPC infrastructure** → Would require Unix socket or TCP bridge + select()
2. **No process pool** → Would require concurrent.futures or multiprocessing
3. **Complexity explosion** → PID management, heartbeat, crash recovery, TTL expiration
4. **MVP ROI** → On-demand LSP covers 90% of use cases; daemon adds 10% perf for 3x complexity
