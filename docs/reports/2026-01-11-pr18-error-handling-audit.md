# Error Handling Audit Report: PR #18 (WO Orchestration Improvements)

**Audit Date**: 2026-01-11
**Auditor**: Claude Code (Error Handling Specialist)
**Scope**: Transaction safety, rollback mechanisms, lock management, and WO orchestration
**Files Reviewed**:
- `scripts/helpers.py` (new functions: heartbeat, lock validity, rollback execution)
- `scripts/ctx_wo_take.py` (modified with transaction wrapper)
- `src/domain/wo_entities.py` (new domain entities)
- `src/domain/wo_transactions.py` (new transaction manager)

---

## Executive Summary

**CRITICAL FINDINGS**: 3 issues that pose immediate production risks
**HIGH SEVERITY**: 4 issues that could cause operational problems
**MEDIUM SEVERITY**: 1 issue affecting maintainability
**LOW SEVERITY**: 2 issues with minimal impact

### Key Problems

1. **"Best-effort" rollback strategy** silently fails, leaving system in corrupted state
2. **Boolean return values** hide error context, preventing proper error recovery
3. **Silent fallbacks** to default values mask underlying system problems
4. **Broad exception catching** hides specific errors that need different handling

### Positive Findings

- Domain layer (`wo_entities.py`, `wo_transactions.py`) correctly uses `Result` types
- `run_command()` has good error logging and re-raises (mostly)
- Transaction design is sound; the execution layer needs improvement

---

## Critical Issues

### CRITICAL-1: Silent Failures in Rollback Execution

**Location**: `scripts/helpers.py:467-541` - `execute_rollback()`

**Issue Description**:
The `execute_rollback()` function uses a "best-effort" strategy that continues attempting rollback even when individual operations fail. While this maximizes cleanup attempts, it creates several critical problems:

```python
# Lines 495-531
for op in reversed(transaction.operations):
    try:
        if op.rollback_type == "remove_lock":
            lock_path.unlink()  # Can fail silently
        elif op.rollback_type == "move_wo_to_pending":
            # YAML operations that can fail
        # ... other operations
    except Exception as e:
        error_msg = f"{op.name}: {type(e).__name__}: {e}"
        logger.error(f"✗ Rollback failed: {error_msg}")
        failed_ops.append(error_msg)
        # CONTINUE anyway - best-effort cleanup  ← PROBLEM
```

**Hidden Errors That Could Be Caught**:
- `PermissionError`: Cannot remove lock file or write to directories
- `FileNotFoundError`: Unexpected missing files (TOCTOU race)
- `yaml.YAMLError`: Corrupted YAML in running WO file
- `subprocess.CalledProcessError`: Git commands failing
- `OSError`: Disk full, network filesystem issues
- `IsADirectoryError`: Path corruption (lock file became directory)

**Production Impact**:
1. **Lock remains acquired**: If lock removal fails, WO cannot be retried
2. **WO stuck in "running" state**: Cannot be taken by another developer
3. **Disk space wasted**: Worktree directories not cleaned up
4. **Git state corrupted**: Branches not removed, cluttering repository
5. **No recovery path**: System requires manual intervention to fix

**Caller Impact** (from `ctx_wo_take.py:250-257`):
```python
all_succeeded, failed_ops = execute_rollback(transaction, root)
if all_succeeded:
    logger.info("✓ Rollback completed")
else:
    logger.error(f"✗ Rollback partially failed: {failed_ops}")
    # Returns 1 anyway - no retry, no alert, no recovery
return 1
```

**Recommendation**:
1. **Change return type from `tuple[bool, list[str]]` to `Result[None, RollbackError]`**
2. **Define specific rollback error types**:
   ```python
   @dataclass(frozen=True)
   class RollbackError:
       failed_operations: list[str]
       requires_manual_intervention: bool
       recovery_steps: list[str]
   ```
3. **Raise exception if critical operations fail**:
   ```python
   CRITICAL_OPS = {"remove_lock", "move_wo_to_pending"}

   for op in reversed(transaction.operations):
       try:
           # ... execute rollback
       except Exception as e:
           failed_ops.append(f"{op.name}: {e}")
           if op.rollback_type in CRITICAL_OPS:
               # Don't continue - critical state is corrupted
               raise RollbackCriticalError(
                   f"Critical rollback failed: {op.name}",
                   failed_ops=failed_ops
               )
   ```
4. **Add recovery suggestions** to rollback errors:
   ```python
   if op.rollback_type == "remove_lock":
       recovery_steps.append(f"Manually remove: {lock_path}")
   elif op.rollback_type == "move_wo_to_pending":
       recovery_steps.append(f"Move {running_path} to {pending_path}")
       recovery_steps.append(f"Reset status: pending, owner: null")
   ```

---

### CRITICAL-2: Lock Heartbeat Returns False Without Error Distinction

**Location**: `scripts/helpers.py:357-407` - `update_lock_heartbeat()`

**Issue Description**:
The function returns `False` on all errors, making it impossible for the caller to distinguish between:
- Lock file doesn't exist (expected - WO finished)
- Permission denied (system error - needs investigation)
- Disk full (system error - needs investigation)
- Filesystem read-only (system error - needs investigation)

```python
# Lines 369-371
if not lock_path.exists():
    logger.warning(f"Lock file not found for heartbeat: {lock_path}")
    return False  # ← Is this an error or expected?

# Lines 394-404
try:
    with open(temp_path, "w") as f:
        f.write('\n'.join(updated_lines))
    os.replace(temp_path, lock_path)
    return True
except Exception as e:
    logger.error(f"Failed to update heartbeat: {e}")
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    return False  # ← Why did it fail?
```

**Hidden Errors**:
- `PermissionError`: Cannot write to lock file or directory
- `FileNotFoundError`: Lock file deleted between exists() check and read()
- `OSError`: Disk full (`ENOSPC`)
- `IOError`: Filesystem issues (NFS timeout, etc.)
- `ValueError`: Invalid datetime format (shouldn't happen)

**Production Impact**:
1. **Heartbeat loop continues silently**: Background process keeps trying to update heartbeat
2. **Lock marked stale prematurely**: If heartbeat fails due to transient error, lock is considered stale and cleaned up
3. **Active WO interrupted**: Developer loses their lock while working
4. **No alerting**: Operator doesn't know heartbeat is failing
5. **Log flood**: Continuous error messages create noise

**Recommendation**:
1. **Return `Result[None, HeartbeatError]`** instead of bool:
   ```python
   @dataclass(frozen=True)
   class HeartbeatError:
       reason: str  # "lock_not_found", "permission_denied", etc.
       recoverable: bool  # Can retry?
       original_error: Exception

   def update_lock_heartbeat(lock_path: Path) -> Result[None, HeartbeatError]:
       if not lock_path.exists():
           return Err(HeartbeatError(
               reason="lock_not_found",
               recoverable=False,
               original_error=FileNotFoundError(str(lock_path))
           ))
       # ... try update
       except PermissionError as e:
           return Err(HeartbeatError(
               reason="permission_denied",
               recoverable=False,  # Don't retry
               original_error=e
           ))
       except OSError as e:
           if e.errno == errno.ENOSPC:
               return Err(HeartbeatError(
                   reason="disk_full",
                   recoverable=False,
                   original_error=e
               ))
           return Err(HeartbeatError(
               reason="io_error",
               recoverable=True,  # Transient - retry
               original_error=e
           ))
   ```

2. **Caller should handle based on error type**:
   ```python
   result = update_lock_heartbeat(lock_path)
   if result.is_err():
       error = result.error
       if not error.recoverable:
           logger.critical(f"Fatal heartbeat error: {error.reason}")
           alert_operator(f"Heartbeat failed: {error.reason}")
           sys.exit(1)
       else:
           logger.warning(f"Transient heartbeat error: {error.reason}, retrying...")
   ```

---

### CRITICAL-3: Lock Validity Check Hides Error Types

**Location**: `scripts/helpers.py:410-464` - `check_lock_validity()`

**Issue Description**:
The function returns `(False, None)` for both expected cases (lock doesn't exist) and error cases (permission denied, corrupted file). This makes it impossible to distinguish between:

```python
# Lines 427-428
if not lock_path.exists():
    return False, None  # Expected: lock doesn't exist

# Lines 459-464
except (OSError, ValueError) as e:
    logger.error(f"Error parsing lock metadata: {type(e).__name__}: {e}")
    return False, None  # ← Error: can't read lock file
except Exception as e:
    logger.error(f"Unexpected error reading lock: {type(e).__name__}: {e}")
    return False, None  # ← Error: unexpected issue
```

**Hidden Errors**:
- `PermissionError`: Cannot read lock file (should alert, not ignore)
- `IsADirectoryError`: Lock path is a directory (corruption - needs cleanup)
- `UnicodeDecodeError`: Lock file has invalid encoding
- `OSError`: Disk corruption, network filesystem issues
- `ValueError`: PID is not an integer (lock file malformed)

**Production Impact**:
1. **Lock considered "invalid" on permission errors**: Lock might be removed even though it's valid
2. **Active WO interrupted**: Developer loses lock due to filesystem permission issue
3. **Corruption undetected**: Lock file became directory but is treated as "doesn't exist"
4. **Race condition**: Lock file deleted between exists() check and read() - treated as expected instead of race

**Recommendation**:
1. **Return `Result[LockMetadata, LockCheckError]`**:
   ```python
   @dataclass(frozen=True)
   class LockMetadata:
       pid: int
       user: str
       hostname: str
       created_at: datetime
       heartbeat_at: Optional[datetime]

   @dataclass(frozen=True)
   class LockCheckError:
       reason: str  # "not_found", "stale", "permission_denied", "corrupted"
       is_recoverable: bool
       original_error: Optional[Exception]

   def check_lock_validity(lock_path: Path) -> Result[LockMetadata, LockCheckError]:
       if not lock_path.exists():
           return Err(LockCheckError(
               reason="not_found",
               is_recoverable=True,
               original_error=None
           ))

       if check_lock_age(lock_path):
           return Err(LockCheckError(
               reason="stale",
               is_recoverable=True,
               original_error=None
           ))

       try:
           content = lock_path.read_text()
           # ... parse metadata
           pid = int(metadata["PID"])
           os.kill(pid, 0)
           return Ok(LockMetadata(...))
       except PermissionError as e:
           logger.critical(f"Permission denied reading lock: {lock_path}")
           return Err(LockCheckError(
               reason="permission_denied",
               is_recoverable=False,
               original_error=e
           ))
       except (ValueError, KeyError) as e:
           logger.error(f"Corrupted lock file: {lock_path} - {e}")
           return Err(LockCheckError(
               reason="corrupted",
               is_recoverable=False,
               original_error=e
           ))
   ```

2. **Caller should handle based on error reason**:
   ```python
   result = check_lock_validity(lock_path)
   if result.is_err():
       error = result.error
       if error.reason == "not_found":
           logger.info("Lock available")
       elif error.reason == "stale":
           logger.info("Lock is stale, can be cleaned up")
           cleanup_stale_lock(lock_path)
       elif error.reason == "permission_denied":
           logger.critical(f"Cannot read lock: {lock_path}")
           alert_operator(f"Permission denied: {lock_path}")
           return 1
       elif error.reason == "corrupted":
           logger.error(f"Corrupted lock: {lock_path}")
           alert_operator(f"Lock file corrupted: {lock_path}")
           return 1
   ```

---

## High Severity Issues

### HIGH-1: Silent Fallback to Default Branch

**Location**: `scripts/helpers.py:96-121` - `git_get_default_branch()`

**Issue Description**:
The function silently falls back to `DEFAULT_BRANCH` constant without validating that the branch exists. This hides git configuration problems and produces cryptic downstream errors.

```python
# Lines 99-108
try:
    result = run_command(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=root,
        check=False
    )
    if result.returncode == 0:
        return result.stdout.strip().split("/")[-1]
except Exception:  # ← Silent failure - no logging!
    pass

# Lines 110-120
for branch in ["main", "master"]:
    result = run_command(
        ["git", "rev-parse", "--verify", branch],
        cwd=root,
        check=False
    )
    if result.returncode == 0:
        return branch

# Line 121
return DEFAULT_BRANCH  # ← "main" might not exist!
```

**Hidden Errors**:
- `subprocess.CalledProcessError`: Git commands failing (silently caught)
- `FileNotFoundError`: Git not installed or not in PATH
- `PermissionError`: Cannot access git repository
- `OSError`: Network filesystem issues
- Git repository corruption
- Missing origin remote

**Production Impact**:
1. **Cryptic downstream errors**: Caller tries to use "main" branch and fails with "branch not found"
2. **No debugging context**: Error occurs far from the root cause
3. **Incorrect assumptions**: Code assumes "main" exists, breaks on repositories using "master" or other names
4. **No alerting**: Git configuration problems go unnoticed

**Recommendation**:
1. **Add logging for fallback attempts**:
   ```python
   try:
       result = run_command(
           ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
           cwd=root,
           check=False
       )
       if result.returncode == 0:
           return result.stdout.strip().split("/")[-1]
   except Exception as e:
       logger.warning(f"Cannot get default branch from origin: {e}")
       # Continue to fallback
   ```

2. **Validate DEFAULT_BRANCH before returning**:
   ```python
   # Validate DEFAULT_BRANCH exists
   result = run_command(
       ["git", "rev-parse", "--verify", DEFAULT_BRANCH],
       cwd=root,
       check=False
   )
   if result.returncode != 0:
       raise RuntimeError(
           f"Cannot determine default branch. "
           f"Tried origin/HEAD, main, master, and {DEFAULT_BRANCH}. "
           f"Please set origin/HEAD or create a default branch."
       )
   return DEFAULT_BRANCH
   ```

3. **Consider returning `Result[str, GitError]`**:
   ```python
   def git_get_default_branch(root: Path) -> Result[str, GitError]:
       """Get default branch or return error if cannot be determined."""
       # ... try multiple methods
       raise GitError(
           "Cannot determine default branch",
           suggestions=["Create 'main' or 'master' branch", "Set origin/HEAD"]
       )
   ```

---

### HIGH-2: Worktree Creation Loses Error Context

**Location**: `scripts/helpers.py:124-211` - `create_worktree()`

**Issue Description**:
When worktree creation fails, the exception propagates without context about which WO, branch, or path was being used. This makes debugging difficult.

```python
# Lines 199-208
if branch_exists:
    logger.info(f"  Branch {branch} already exists, using it")
    run_command(
        ["git", "worktree", "add", str(worktree_path), branch],
        cwd=root
    )
else:
    logger.info(f"  Creating new branch {branch} from {default_branch}")
    run_command(
        ["git", "worktree", "add", "-b", branch, str(worktree_path), default_branch],
        cwd=root
    )
# ← If run_command raises, no context about wo_id, branch, or path
```

**Hidden Errors**:
- `subprocess.CalledProcessError`: Git worktree add fails (but why?)
- `PermissionError`: Cannot create worktree directory
- `OSError`: Disk full, quota exceeded
- `FileExistsError`: Worktree path already exists (TOCTOU race)

**Production Impact**:
1. **Cryptic error messages**: "Command failed: git worktree add .worktrees/WO-0012"
2. **No debugging context**: Developer doesn't know which WO, branch, or base branch
3. **Cannot reproduce**: Error message doesn't have enough information to reproduce
4. **No recovery suggestions**: Doesn't tell developer how to fix the problem

**Recommendation**:
1. **Wrap run_command calls with context**:
   ```python
   try:
       if branch_exists:
           logger.info(f"  Branch {branch} already exists, using it")
           run_command(
               ["git", "worktree", "add", str(worktree_path), branch],
               cwd=root
           )
       else:
           logger.info(f"  Creating new branch {branch} from {default_branch}")
           run_command(
               ["git", "worktree", "add", "-b", branch, str(worktree_path), default_branch],
               cwd=root
           )
   except subprocess.CalledProcessError as e:
       raise WorktreeCreationError(
           f"Failed to create worktree for WO {wo_id}",
           wo_id=wo_id,
           branch=branch,
           worktree_path=worktree_path,
           base_branch=default_branch,
           git_error=e.stderr,
           suggestions=[
               f"Check if {worktree_path} already exists",
               f"Verify branch {default_branch} exists",
               "Check disk space and permissions"
           ]
       ) from e
   ```

2. **Define WorktreeCreationError exception class**:
   ```python
   @dataclass
   class WorktreeCreationError(Exception):
       message: str
       wo_id: str
       branch: str
       worktree_path: Path
       base_branch: str
       git_error: str
       suggestions: list[str]

       def __str__(self):
           return f"{self.message}\n" + \
                  f"  WO: {self.wo_id}\n" + \
                  f"  Branch: {self.branch}\n" + \
                  f"  Path: {self.worktree_path}\n" + \
                  f"  Base branch: {self.base_branch}\n" + \
                  f"  Git error: {self.git_error}\n" + \
                  f"  Suggestions:\n" + "\n".join(f"    - {s}" for s in self.suggestions)
   ```

---

### HIGH-3: Cleanup Returns False Without Indicating What Failed

**Location**: `scripts/helpers.py:214-247` - `cleanup_worktree()`

**Issue Description**:
The function returns `False` on any error, making it impossible to know which cleanup step failed or why.

```python
# Lines 228-247
try:
    if worktree_path.exists():
        logger.info(f"Removing worktree: {worktree_path}")
        run_command(["git", "worktree", "remove", str(worktree_path)], cwd=root)

    run_command(["git", "worktree", "prune"], cwd=root)

    try:
        run_command(["git", "branch", "-D", branch], cwd=root, check=False)
        logger.info(f"Removed branch: {branch}")
    except Exception:
        logger.info(f"Branch {branch} not removed (may not exist)")

    return True
except Exception as e:
    logger.error(f"Failed to cleanup worktree: {e}")
    return False  # ← What failed? Why?
```

**Hidden Errors**:
- `subprocess.CalledProcessError`: Git worktree remove fails
- `PermissionError`: Cannot remove worktree directory
- `FileNotFoundError`: Worktree path doesn't exist (TOCTOU)
- `OSError`: Worktree is not empty (files left behind)
- Git corruption: Worktree list inconsistent

**Production Impact**:
1. **Cannot recover**: Caller doesn't know what to clean up manually
2. **No debugging context**: Don't know which WO failed cleanup
3. **Silent partial failures**: Branch removal failure is ignored but other failures aren't (inconsistent)

**Recommendation**:
1. **Return `Result[None, CleanupError]`**:
   ```python
   @dataclass(frozen=True)
   class CleanupError:
       wo_id: str
       worktree_removal_failed: bool = False
       branch_removal_failed: bool = False
       worktree_path: Optional[Path] = None
       branch: Optional[str] = None
       original_error: Optional[Exception] = None

       def requires_manual_cleanup(self) -> bool:
           return self.worktree_removal_failed or self.branch_removal_failed

       def get_manual_cleanup_commands(self) -> list[str]:
           commands = []
           if self.worktree_removal_failed and self.worktree_path:
               commands.append(f"git worktree remove -f {self.worktree_path}")
               commands.append(f"rm -rf {self.worktree_path}")
           if self.branch_removal_failed and self.branch:
               commands.append(f"git branch -D {self.branch}")
           return commands

   def cleanup_worktree(root: Path, wo_id: str) -> Result[None, CleanupError]:
       worktree_path = get_worktree_path(wo_id, root)
       branch = get_branch_name(wo_id)

       worktree_failed = False
       branch_failed = False
       original_error = None

       try:
           if worktree_path.exists():
               logger.info(f"Removing worktree: {worktree_path}")
               try:
                   run_command(["git", "worktree", "remove", str(worktree_path)], cwd=root)
               except Exception as e:
                   logger.error(f"Failed to remove worktree: {e}")
                   worktree_failed = True
                   original_error = e

           run_command(["git", "worktree", "prune"], cwd=root)

           try:
               run_command(["git", "branch", "-D", branch], cwd=root, check=False)
               logger.info(f"Removed branch: {branch}")
           except Exception as e:
               logger.info(f"Branch {branch} not removed (may not exist)")

           if worktree_failed:
               return Err(CleanupError(
                   wo_id=wo_id,
                   worktree_removal_failed=worktree_failed,
                   branch_removal_failed=branch_failed,
                   worktree_path=worktree_path,
                   branch=branch,
                   original_error=original_error
               ))
           return Ok(None)
       except Exception as e:
           logger.error(f"Unexpected cleanup error: {e}")
           return Err(CleanupError(
               wo_id=wo_id,
               worktree_removal_failed=True,
               branch_removal_failed=True,
               worktree_path=worktree_path,
               branch=branch,
               original_error=e
           ))
   ```

2. **Caller should handle cleanup errors**:
   ```python
   result = cleanup_worktree(root, wo_id)
   if result.is_err():
       error = result.error
       logger.warning(f"Cleanup failed for WO {wo_id}")
       if error.requires_manual_cleanup():
           logger.error("Manual cleanup required:")
           for cmd in error.get_manual_cleanup_commands():
               logger.error(f"  {cmd}")
   ```

---

### HIGH-4: Lock Creation Returns False for Multiple Failure Modes

**Location**: `scripts/helpers.py:280-335` - `create_lock()`

**Issue Description**:
The function returns `False` for all failure modes, making it impossible to distinguish between "already locked" (expected, retry later) and "error" (alert operator).

```python
# Lines 295-297
if lock_path.exists():
    logger.warning(f"Lock already exists: {lock_path}")
    return False  # ← Expected: already locked

# Lines 316-330
try:
    os.link(temp_path, lock_path)
    os.unlink(temp_path)
    return True
except OSError:
    try:
        os.rename(temp_path, lock_path)
        return True
    except OSError:
        os.unlink(temp_path)
        logger.warning(f"Failed to acquire lock: {lock_path}")
        return False  # ← Error: permission denied? disk full?

# Lines 331-335
except Exception as e:
    logger.error(f"Error creating lock: {e}")
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    return False  # ← Error: unexpected
```

**Hidden Errors**:
- `FileExistsError`: Lock created between exists() check and link() (race condition)
- `PermissionError`: Cannot create lock file
- `OSError.ENOSPC`: Disk full
- `OSError.EROFS`: Read-only filesystem
- `OSError.EOPNOTSUPP`: Hard links not supported, rename also failed

**Production Impact**:
1. **Cannot distinguish retry vs error**: Caller treats "already locked" same as "permission denied"
2. **No alerting**: Permission errors go to log but don't alert operator
3. **Incorrect retry behavior**: Might retry when shouldn't (permission error)
4. **Race conditions**: Lock created between check and link() not detected

**Recommendation**:
1. **Return `Result[None, LockError]`**:
   ```python
   @dataclass(frozen=True)
   class LockError:
       reason: str  # "already_exists", "permission_denied", "disk_full", etc.
       recoverable: bool  # Can retry?
       original_error: Optional[Exception]

   def create_lock(lock_path: Path, wo_id: str) -> Result[None, LockError]:
       if lock_path.exists():
           logger.warning(f"Lock already exists: {lock_path}")
           return Err(LockError(
               reason="already_exists",
               recoverable=True,  # Retry later
               original_error=None
           ))

       temp_fd, temp_path = tempfile.mkstemp(
           prefix=f"{wo_id}.",
           suffix=".lock",
           dir=lock_path.parent
       )
       os.close(temp_fd)

       try:
           # Write metadata
           with open(temp_path, "w") as f:
               f.write(f"Locked by ctx_wo_take.py at {datetime.now(timezone.utc).isoformat()}\n")
               f.write(f"PID: {os.getpid()}\n")
               f.write(f"User: {getpass.getuser()}\n")
               f.write(f"Hostname: {os.uname().nodename}\n")

           # Try atomic operations
           try:
               os.link(temp_path, lock_path)
               os.unlink(temp_path)
               return Ok(None)
           except OSError as e:
               # Check specific error codes
               if e.errno == errno.EEXIST:
                   # Lock created between exists() check and link()
                   os.unlink(temp_path)
                   return Err(LockError(
                       reason="already_exists",
                       recoverable=True,
                       original_error=e
                   ))
               elif e.errno == errno.EOPNOTSUPP:
                   # Hard links not supported, try rename
                   try:
                       os.rename(temp_path, lock_path)
                       return Ok(None)
                   except OSError as e2:
                       os.unlink(temp_path)
                       if e2.errno == errno.ENOSPC:
                           return Err(LockError(
                               reason="disk_full",
                               recoverable=False,
                               original_error=e2
                           ))
                       elif e2.errno in (errno.EACCES, errno.EPERM):
                           return Err(LockError(
                               reason="permission_denied",
                               recoverable=False,
                               original_error=e2
                           ))
                       raise
               elif e.errno in (errno.EACCES, errno.EPERM):
                   os.unlink(temp_path)
                   return Err(LockError(
                       reason="permission_denied",
                       recoverable=False,
                       original_error=e
                   ))
               elif e.errno == errno.ENOSPC:
                   os.unlink(temp_path)
                   return Err(LockError(
                       reason="disk_full",
                       recoverable=False,
                       original_error=e
                   ))
               raise
       except Exception as e:
           logger.error(f"Error creating lock: {e}")
           if os.path.exists(temp_path):
               os.unlink(temp_path)
           return Err(LockError(
               reason="unknown",
               recoverable=False,
               original_error=e
           ))
   ```

2. **Caller should handle based on error reason**:
   ```python
   result = create_lock(lock_path, wo_id)
   if result.is_err():
       error = result.error
       if error.reason == "already_exists":
           logger.warning(f"WO {wo_id} is already locked")
           return 1
       elif error.reason == "permission_denied":
           logger.critical(f"Permission denied creating lock for {wo_id}")
           alert_operator(f"Cannot create lock: {lock_path}")
           return 1
       elif error.reason == "disk_full":
           logger.critical("Disk full - cannot create lock")
           alert_operator("Disk full on lock filesystem")
           return 1
   ```

---

## Medium Severity Issues

### MEDIUM-1: Transaction Wrapper Uses Broad Exception Catching

**Location**: `scripts/ctx_wo_take.py:239-296` - Transaction wrapper in `take()` command

**Issue Description**:
The transaction wrapper catches `Exception` in multiple places, which is too broad and hides unexpected errors.

```python
# Lines 239-258: Worktree creation
try:
    logger.info(f"Creating worktree for {wo_id}...")
    create_worktree(root, wo_id, branch, Path(worktree))
    # Add rollback operations
except Exception as e:  # ← Too broad
    logger.error(f"Failed to create worktree: {e}")
    logger.info("Executing rollback...")
    all_succeeded, failed_ops = execute_rollback(transaction, root)
    if all_succeeded:
        logger.info("✓ Rollback completed")
    else:
        logger.error(f"✗ Rollback partially failed: {failed_ops}")
    return 1

# Lines 269-285: Move WO to running
try:
    write_yaml(running_path, wo)
    job_path.unlink()
except Exception as e:  # ← Too broad
    # Same rollback pattern

# Lines 287-296: Outer handler
except Exception as e:  # ← Very broad
    logger.error(f"Unexpected error during WO take: {e}")
    # Same rollback pattern
```

**Hidden Errors**:
- `KeyboardInterrupt`: User pressed Ctrl+C (should abort immediately, not rollback)
- `MemoryError`: Out of memory (rollback might also fail)
- `SystemExit`: sys.exit() called (should exit immediately)
- `yaml.YAMLError`: Corrupted YAML (specific error needed)
- `FileNotFoundError`: WO file deleted (specific error needed)
- `PermissionError`: Cannot write to directories (specific error needed)

**Production Impact**:
1. **Unexpected errors treated as expected**: SystemExit, KeyboardInterrupt trigger rollback
2. **No debugging context**: Generic "Failed to create worktree" doesn't help
3. **Rollback might also fail**: If original error was resource exhaustion, rollback will also fail
4. **Inconsistent handling**: Some exceptions should abort immediately (KeyboardInterrupt)

**Recommendation**:
1. **Catch specific exceptions**:
   ```python
   # Worktree creation
   try:
       logger.info(f"Creating worktree for {wo_id}...")
       create_worktree(root, wo_id, branch, Path(worktree))
       transaction = transaction.add_operation(...)
   except (WorktreeCreationError, subprocess.CalledProcessError) as e:
       logger.error(f"Failed to create worktree: {e}")
       logger.info("Executing rollback...")
       all_succeeded, failed_ops = execute_rollback(transaction, root)
       if not all_succeeded:
           logger.error(f"✗ Rollback partially failed: {failed_ops}")
       return 1
   except Exception as e:
       # Unexpected error - still rollback but log as critical
       logger.critical(f"Unexpected error creating worktree: {type(e).__name__}: {e}")
       logger.info("Executing rollback...")
       execute_rollback(transaction, root)
       raise  # Re-raise to expose the unexpected error

   # Move WO to running
   try:
       write_yaml(running_path, wo)
       job_path.unlink()
   except (yaml.YAMLError, PermissionError, OSError) as e:
       logger.error(f"Failed to move WO to running: {e}")
       logger.info("Executing rollback...")
       execute_rollback(transaction, root)
       return 1

   # Outer handler - only catch expected errors
   try:
       # ... WO take logic
   except KeyboardInterrupt:
       logger.warning("WO take interrupted by user")
       logger.info("Executing rollback...")
       execute_rollback(transaction, root)
       sys.exit(130)  # Standard exit code for SIGINT
   except (WorktreeCreationError, yaml.YAMLError, PermissionError, OSError) as e:
       logger.error(f"WO take failed: {e}")
       logger.info("Executing rollback...")
       execute_rollback(transaction, root)
       return 1
   ```

2. **Don't catch Exception in outer handler**:
   ```python
   # Let unexpected errors propagate
   # They will be caught by the main() handler which logs and exits
   ```

---

## Low Severity Issues

### LOW-1: run_command() Lacks Timeout

**Location**: `scripts/helpers.py:61-87` - `run_command()`

**Issue Description**:
The function has no timeout parameter, so commands can hang forever.

```python
# Lines 74-81
logger.debug(f"Running: {' '.join(cmd)}")
try:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True
        # ← No timeout!
    )
```

**Hidden Errors**:
- Command hangs forever (e.g., waiting for user input, network timeout)
- No way to cancel long-running operations

**Production Impact**:
1. **Process hangs**: WO take script hangs waiting for git command
2. **No recovery**: Must kill process manually
3. **Lock timeout**: If heartbeat is running, lock might be marked stale

**Recommendation**:
```python
def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    timeout: Optional[int] = 300  # Default 5 minutes
) -> subprocess.CompletedProcess:
    logger.debug(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise
```

---

### LOW-2: list_worktrees() Doesn't Validate Git Output

**Location**: `scripts/helpers.py:250-277` - `list_worktrees()`

**Issue Description**:
The function assumes git output format is correct and doesn't handle malformed output.

```python
# Lines 264-272
for line in result.stdout.splitlines():
    if not line:
        if current:
            worktrees.append(current)
            current = {}
        continue

    key, value = line.split(" ", 1)  # ← Assumes format "KEY value"
    current[key] = value
```

**Hidden Errors**:
- `ValueError`: Line has no spaces (split fails)
- Git output format changes (future compatibility)
- UnicodeDecodeError: Invalid encoding in output

**Production Impact**:
1. **Cryptic error**: "not enough values to unpack" doesn't help debugging
2. **No validation**: Worktree paths might not exist

**Recommendation**:
```python
def list_worktrees(root: Path) -> list[dict]:
    """List all git worktrees."""
    result = run_command(["git", "worktree", "list", "--porcelain"], cwd=root)

    worktrees = []
    current = {}

    for line_num, line in enumerate(result.stdout.splitlines(), 1):
        if not line:
            if current:
                # Validate worktree path exists
                if "worktree" in current:
                    worktree_path = Path(current["worktree"])
                    if not worktree_path.exists():
                        logger.warning(
                            f"Worktree path doesn't exist: {worktree_path} "
                            f"(line {line_num})"
                        )
                worktrees.append(current)
                current = {}
            continue

        # Validate line format
        if " " not in line:
            logger.warning(f"Malformed git worktree output line {line_num}: {line}")
            continue

        key, value = line.split(" ", 1)
        current[key] = value

    if current:
        worktrees.append(current)

    return worktrees
```

---

## Summary and Recommendations

### Critical Actions (Do Immediately)

1. **Fix `execute_rollback()`**:
   - Stop using "best-effort" strategy for critical operations
   - Raise exception if lock removal or WO state change fails
   - Return `Result` type instead of `(bool, list[str])`

2. **Fix `update_lock_heartbeat()`**:
   - Return `Result` type with specific error reasons
   - Caller should abort on non-recoverable errors
   - Don't silently continue on permission errors

3. **Fix `check_lock_validity()`**:
   - Return `Result[LockMetadata, LockCheckError]`
   - Distinguish between "not found" and "permission denied"
   - Alert operator on permission errors

### High Priority Actions

4. **Fix `git_get_default_branch()`**:
   - Validate DEFAULT_BRANCH exists before returning
   - Add logging for fallback attempts
   - Raise exception if cannot determine default branch

5. **Fix `create_worktree()`**:
   - Wrap exceptions with context (WO ID, branch, path)
   - Define `WorktreeCreationError` with suggestions
   - Add recovery steps to error message

6. **Fix `cleanup_worktree()`**:
   - Return `Result[None, CleanupError]`
   - Indicate which operations failed
   - Provide manual cleanup commands

7. **Fix `create_lock()`**:
   - Return `Result[None, LockError]`
   - Distinguish between "already exists" and "permission denied"
   - Check errno for specific error types

### Medium Priority Actions

8. **Fix transaction wrapper in `ctx_wo_take.py`**:
   - Catch specific exceptions instead of `Exception`
   - Handle KeyboardInterrupt separately
   - Re-raise unexpected errors after rollback

### Low Priority Actions

9. **Add timeout to `run_command()`**:
   - Default timeout of 5 minutes
   - Catch `TimeoutExpired` and log

10. **Validate git output in `list_worktrees()`**:
    - Handle malformed lines gracefully
    - Validate worktree paths exist

### General Recommendations

1. **Adopt Result types throughout infrastructure layer**:
   - The domain layer shows the right pattern
   - Use `Result[T, E]` instead of `bool` or `tuple[bool, ...]`
   - Define specific error types for each operation

2. **Add context to exceptions**:
   - When catching and re-raising, add context (WO ID, paths, etc.)
   - Use exception chaining (`raise ... from e`)
   - Include recovery suggestions in error messages

3. **Never silently ignore critical failures**:
   - Lock operations, WO state changes must succeed or raise
   - Don't use "best-effort" for state-changing operations
   - If rollback fails, system is in inconsistent state - alert operator

4. **Distinguish between recoverable and non-recoverable errors**:
   - "Lock already exists" → recoverable (retry later)
   - "Permission denied" → non-recoverable (alert operator)
   - Use different error types or error reasons

5. **Add structured logging**:
   - Include WO ID, operation name, paths in all error logs
   - Use log levels appropriately (warning for expected, error for unexpected, critical for non-recoverable)
   - Add error IDs for Sentry tracking

---

## Testing Recommendations

Add tests for error handling:

```python
# tests/unit/test_helpers_error_handling.py

def test_execute_rollback_critical_failure():
    """Test that critical rollback failures raise exceptions."""
    transaction = Transaction(wo_id="WO-001", operations=[
        RollbackOperation(name="acquire_lock", description="", rollback_type="remove_lock"),
        RollbackOperation(name="create_worktree", description="", rollback_type="remove_worktree"),
    ])
    root = Path("/fake")

    # Mock lock removal to fail with permission error
    with patch.object(Path, "unlink") as mock_unlink:
        mock_unlink.side_effect = PermissionError("Cannot remove lock")

        with pytest.raises(RollbackCriticalError) as exc_info:
            execute_rollback(transaction, root)

        assert "remove_lock" in str(exc_info.value)
        assert "PermissionError" in str(exc_info.value)

def test_update_lock_heartbeat_permission_denied():
    """Test that permission errors are non-recoverable."""
    lock_path = Path("/fake/lock")

    with patch.object(Path, "exists", return_value=True):
        with patch.object(Path, "read_text", side_effect=PermissionError("Cannot read")):
            result = update_lock_heartbeat(lock_path)

            assert result.is_err()
            assert result.error.reason == "permission_denied"
            assert result.error.recoverable is False

def test_check_lock_validity_corrupted_file():
    """Test that corrupted lock files are detected."""
    lock_path = Path("/fake/lock")

    with patch.object(Path, "exists", return_value=True):
        with patch.object(Path, "read_text", return_value="PID: not_a_number"):
            result = check_lock_validity(lock_path)

            assert result.is_err()
            assert result.error.reason == "corrupted"
```

---

## Conclusion

The PR introduces good transaction design concepts from the domain layer, but the infrastructure layer execution has several critical error handling issues:

1. **Silent failures**: "Best-effort" rollback hides failures
2. **Inadequate error context**: Boolean returns don't distinguish error types
3. **Inappropriate fallbacks**: Default values mask underlying problems

The domain layer (`wo_entities.py`, `wo_transactions.py`) correctly uses `Result` types and should be the model for the infrastructure layer.

**Risk Assessment**: HIGH - Silent failures in production could cause WOs to be stuck in running state, locks to not be released, and require manual intervention to recover.

**Recommendation**: Address CRITICAL issues before merging to production. HIGH and MEDIUM issues should be fixed in follow-up PRs. LOW issues can be deferred.

---

**Audit Completed**: 2026-01-11
**Next Review**: After fixes are implemented
