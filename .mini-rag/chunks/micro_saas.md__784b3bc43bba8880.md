### PROMPT: IMPLEMENT SECURE MANIFEST & LOCKING (SHA-256)

**Role:** Security Architect.

**Context:**
We are implementing a **Secure Local Dependency System** for Trifecta Skills.
To prevent Supply Chain attacks (unintended changes in source files), we will use a **Content-Addressable Locking mechanism** (SHA-256).

**Architecture Rules:**

1. **Manifest (`trifecta.yaml`):** Declares intent (path to file).
2. **Lockfile (`trifecta.lock`):** Stores the approved SHA-256 hash of the content.
3. **Strict Verification:** The builder MUST fail if the current file content hash does not match the lockfile hash.
4. **Explicit Update:** Only a dedicated `update` command can write to the lockfile.

**Mission:**
Implement the Domain Models and Logic to support this security protocol.

**Tasks:**

1. **Create `src/domain/security.py`:**
* Function `calculate_file_hash(path: Path) -> str`: Returns SHA-256 hex digest.


2. **Create `src/domain/manifest.py`:**
* `SkillEntry`: `name` (str), `path` (Path).
* `LockEntry`: `name` (str), `sha256` (str), `source_path` (str), `updated_at` (datetime).
* `TrifectaManifest`: List of `SkillEntry`.
* `TrifectaLock`: Dict of `name` -> `LockEntry`.


3. **Define Logic (Mock in comments):**
* Explain how `validate_integrity(manifest, lock)` will work.
* Explain how `update_lock(manifest)` will work.
