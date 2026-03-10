---
name: trifecta-daemon
description: Use and manage Trifecta daemon for long-running operations
version: 1.0.0
source: local-git-analysis
analyzed_commits: 3
---

# Trifecta Daemon Usage

## Overview

Trifecta daemon provides a background process for repository operations with health monitoring and graceful lifecycle management.

## Quick Start

```bash
# Start daemon for a repository
trifecta daemon start --repo /path/to/repo

# Check daemon status
trifecta daemon status --repo /path/to/repo

# Stop daemon
trifecta daemon stop --repo /path/to/repo

# Restart daemon
trifecta daemon restart --repo /path/to/repo
```

## Architecture

### Components

```
~/.local/share/trifecta/repos/<repo_id>/
├── runtime/
│   └── daemon/
│       ├── socket     # UNIX socket (0600 permissions)
│       ├── pid        # Process ID file
│       └── log        # Daemon stdout/stderr
```

### Security Features

- **Socket Permissions**: 0600 (owner read/write only)
- **Path Validation**: Runtime directory must be in ALLOWED_BASES
- **Input Validation**: Max command size 256 bytes
- **Connection Timeout**: 5 seconds per client
- **Trust Boundary**: Local user only (UNIX socket)

## Protocol

The daemon implements a simple text-based protocol over UNIX sockets.

### Commands

#### 1. PING/PONG (Health Check)

```bash
# Using netcat
echo "PING" | nc -U /path/to/socket
# Response: PONG

# Using Python
import socket
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect("/path/to/socket")
client.sendall(b"PING\n")
response = client.recv(1024)  # b"PONG\n"
client.close()
```

**Purpose**: Basic health check to verify daemon is responding.

#### 2. HEALTH (Detailed Status)

```bash
# Using netcat
echo "HEALTH" | nc -U /path/to/socket
# Response: JSON

# Using Python
import socket, json
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect("/path/to/socket")
client.sendall(b"HEALTH\n")
response = json.loads(client.recv(1024).decode())
# {
#   "status": "ok",
#   "pid": 12345,
#   "uptime": 3600,
#   "version": "1.0.0",
#   "protocol": ["PING", "HEALTH", "SHUTDOWN"]
# }
client.close()
```

**Response Fields**:
- `status`: "ok" if daemon is healthy
- `pid`: Process ID of daemon
- `uptime`: Seconds since daemon started
- `version`: Protocol version
- `protocol`: List of supported commands

#### 3. SHUTDOWN (Graceful Termination)

```bash
# Using netcat
echo "SHUTDOWN" | nc -U /path/to/socket
# Response: OK
# Daemon stops gracefully
```

**Behavior**:
- Daemon responds with "OK"
- Closes socket
- Cleans up PID file
- Exits cleanly

## Use Cases

### 1. Background Indexing

```bash
# Start daemon
trifecta daemon start --repo ~/Developer/myproject

# Check health
trifecta daemon status --repo ~/Developer/myproject

# Daemon is now running and can handle background tasks
```

### 2. Health Monitoring

```python
import socket
import json

def check_daemon_health(socket_path):
    """Check if daemon is healthy."""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(socket_path)
        client.sendall(b"HEALTH\n")
        response = json.loads(client.recv(1024).decode())
        client.close()
        return response["status"] == "ok"
    except:
        return False

# Usage
socket_path = "/Users/username/.local/share/trifecta/repos/abc123/runtime/daemon/socket"
if check_daemon_health(socket_path):
    print("Daemon is healthy")
else:
    print("Daemon is down or unhealthy")
```

### 3. Automated Restarts

```python
import subprocess
import socket
import json

def ensure_daemon_running(repo_path):
    """Ensure daemon is running, restart if needed."""
    # Try to start daemon
    subprocess.run(
        ["trifecta", "daemon", "start", "--repo", repo_path],
        capture_output=True
    )
    
    # Verify it's running
    result = subprocess.run(
        ["trifecta", "daemon", "status", "--repo", repo_path],
        capture_output=True,
        text=True
    )
    
    return "running" in result.stdout

# Usage
ensure_daemon_running("~/Developer/myproject")
```

## Troubleshooting

### Issue: Daemon Won't Start

**Symptoms**:
```bash
$ trifecta daemon start --repo .
Failed to start daemon
```

**Diagnosis**:
```bash
# Check daemon logs
tail -f ~/.local/share/trifecta/repos/<repo_id>/runtime/daemon/log

# Check if process is already running
ps aux | grep trifecta

# Check socket permissions
ls -la ~/.local/share/trifecta/repos/*/runtime/daemon/socket
# Should be: srw------- (0600)
```

**Solutions**:
1. Check runtime directory permissions
2. Verify TRIFECTA_RUNTIME_DIR is valid
3. Kill stale processes: `trifecta daemon stop --repo .`
4. Remove stale socket: `rm ~/.local/share/trifecta/repos/*/runtime/daemon/socket`

### Issue: Socket Permission Denied

**Symptoms**:
```bash
$ echo "PING" | nc -U /path/to/socket
nc:Permission denied
```

**Diagnosis**:
```bash
# Check socket permissions
stat -f "%Lp %N" ~/.local/share/trifecta/repos/*/runtime/daemon/socket
# Should be: 600
```

**Solution**:
- Socket is owner-only (0600) by design
- Must be same user that started daemon
- Check with: `ls -la ~/.local/share/trifecta/repos/*/runtime/daemon/socket`

### Issue: Daemon Not Responding

**Symptoms**:
```bash
$ trifecta daemon status --repo .
Daemon: running
  PID: 12345

$ echo "PING" | nc -U /path/to/socket
# No response
```

**Diagnosis**:
```bash
# Check if process exists
ps -p 12345

# Check daemon log
tail -20 ~/.local/share/trifecta/repos/*/runtime/daemon/log

# Test socket directly
python3 -c "
import socket
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.settimeout(5.0)
client.connect('/path/to/socket')
client.sendall(b'PING\n')
print(client.recv(1024))
"
```

**Solutions**:
1. Restart daemon: `trifecta daemon restart --repo .`
2. Check for zombie processes
3. Review daemon logs for errors

## Integration Examples

### Cron Job Monitoring

```bash
#!/bin/bash
# /usr/local/bin/monitor-trifecta-daemon

REPO_PATH="/path/to/repo"

# Check daemon status
STATUS=$(trifecta daemon status --repo "$REPO_PATH" 2>&1)

if [[ "$STATUS" != *"running"* ]]; then
    echo "Daemon not running, starting..."
    trifecta daemon start --repo "$REPO_PATH"
fi
```

### Python Service Wrapper

```python
import subprocess
import time
from pathlib import Path

class TrifectaDaemon:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        
    def start(self):
        """Start daemon if not running."""
        result = subprocess.run(
            ["trifecta", "daemon", "start", "--repo", self.repo_path],
            capture_output=True, text=True
        )
        return result.returncode == 0
    
    def stop(self):
        """Stop daemon."""
        subprocess.run(
            ["trifecta", "daemon", "stop", "--repo", self.repo_path]
        )
    
    def health_check(self):
        """Check daemon health via PING."""
        socket_path = self._get_socket_path()
        try:
            import socket
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(5.0)
            client.connect(str(socket_path))
            client.sendall(b"PING\n")
            response = client.recv(1024)
            client.close()
            return response == b"PONG\n"
        except:
            return False
    
    def _get_socket_path(self):
        # Implementation depends on repo fingerprint
        return Path.home() / ".local/share/trifecta/repos/*/runtime/daemon/socket"

# Usage
daemon = TrifectaDaemon("/path/to/repo")
if not daemon.health_check():
    daemon.start()
```

## Best Practices

1. **Health Checks**: Always check daemon health before assuming it's ready
2. **Timeouts**: Use 5-second timeout for socket operations
3. **Error Handling**: Handle connection failures gracefully
4. **Cleanup**: Stop daemon when done (if long-running)
5. **Logging**: Monitor daemon logs for issues

## Security Considerations

### What's Protected

- **Socket Access**: 0600 permissions (owner only)
- **Path Validation**: Runtime directory validated against ALLOWED_BASES
- **Input Size**: Max 256 bytes per command
- **Connection Timeout**: 5-second timeout prevents hanging

### Trust Boundaries

- **Local Only**: Daemon only accessible via UNIX socket (no network)
- **Single User**: Only process owner can connect
- **No Authentication**: Relies on file system permissions

### Acceptable Risks

- **No Rate Limiting**: Acceptable for local daemon
- **No Encryption**: UNIX sockets are already secure locally
- **No Auth Tokens**: File permissions provide sufficient security

## Related Commands

- `trifecta status --repo <path>` - Check repository status
- `trifecta doctor --repo <path>` - Run diagnostics
- `trifecta index --repo <path>` - Index repository
- `trifecta query <query> --repo <path>` - Search indexed content

## References

- **Source Code**: `src/infrastructure/cli.py` (daemon_run function)
- **Manager**: `src/platform/daemon_manager.py`
- **Tests**: `tests/integration/daemon/test_daemon_manager.py`
- **Security Audit**: `_ctx/checkpoints/2026-03-06/checkpoint_184423_daemon-security-hardening.md`

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-06  
**Commits Analyzed**: 3 (f57dc5d, 90b8729, 8e169b2)
