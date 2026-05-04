# Bootstrap Safety Contract

## Principles
All automated configuration changes performed by Trifecta MUST be safe, reversible, and transparent.

## Constraints

### 1. Mandatory Dry-Run
- The bootstrap command MUST support a `--dry-run` flag.
- When in dry-run, no filesystem mutations are allowed.
- The output SHALL show a diff of the intended changes.

### 2. Pre-mutation Backup
- Before modifying any configuration file, a backup MUST be created (e.g., `config.json.bak`).
- Backup paths SHALL be reported to the user.

### 3. Change Validation
- Configuration files MUST be validated as valid JSON/YAML before reading.
- After mutation, the resulting content MUST be validated again before writing to disk.

### 4. Atomic Writing
- Writes MUST use a temporary file first, then be renamed to the target path (atomic rename).
- This prevents partial writes if the process is interrupted.

### 5. Idempotency
- Running the bootstrap command multiple times MUST NOT create duplicate MCP entries.
- If a configuration already exists and matches the target state, no write SHALL occur.

### 6. Rollback Capability
- If a write or validation fails, the system MUST attempt to restore from the backup.
- A manual `--rollback` flag SHOULD be available to revert the last bootstrap session.

### 7. Permissions & Paths
- The system MUST check for write permissions before attempting to write.
- Missing directories SHALL NOT be created unless they are part of the standard Trifecta structure (`_ctx`).
- Agent config directories MUST exist; the installer SHALL NOT create them if they are missing (to avoid phantom installs).
