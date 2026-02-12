#!/usr/bin/env python3
"""
Test harness for WO orchestration with automatic worktree creation.

Tests the integration between:
- helpers.py (worktree, lock, branch generation)
- ctx_wo_take.py (WO take workflow)
"""

import sys
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from helpers import (  # noqa: E402
    get_branch_name,
    get_worktree_path,
    create_worktree,
    create_lock,
    check_lock_age,
    cleanup_worktree,
    list_worktrees,
    run_command,
    logger,
)


class WOOrchestrationTest:
    """Test harness for WO orchestration."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.test_wo_id = "WO-9999"  # Use test ID that won't conflict
        self.cleanup_done = False

    def setup(self):
        """Setup test environment."""
        logger.info("Setting up test environment...")

        # Check we're in a git repo
        result = run_command(["git", "rev-parse", "--git-dir"], cwd=self.repo_root)
        if result.returncode != 0:
            logger.error("Not in a git repository")
            return False

        logger.info(f"✓ Git repository: {self.repo_root}")
        return True

    def teardown(self):
        """Cleanup test artifacts."""
        if self.cleanup_done:
            return

        logger.info("Cleaning up test artifacts...")

        # Remove test worktree
        worktree_path = get_worktree_path(self.test_wo_id, self.repo_root)
        if worktree_path.exists():
            logger.info(f"Removing worktree: {worktree_path}")
            try:
                cleanup_worktree(self.repo_root, self.test_wo_id)
            except Exception as e:
                logger.warning(f"Failed to cleanup worktree: {e}")

        # Remove test lock
        lock_path = self.repo_root / "_ctx" / "jobs" / "running" / f"{self.test_wo_id}.lock"
        if lock_path.exists():
            lock_path.unlink()
            logger.info(f"Removed lock: {lock_path}")

        self.cleanup_done = True

    def test_branch_generation(self) -> bool:
        """Test automatic branch name generation."""
        logger.info("Testing branch name generation...")

        branch = get_branch_name(self.test_wo_id)
        expected = f"feat/wo-{self.test_wo_id}"

        if branch == expected:
            logger.info(f"✓ Branch generation: {branch}")
            return True
        else:
            logger.error(f"✗ Branch generation failed: expected {expected}, got {branch}")
            return False

    def test_worktree_path_generation(self) -> bool:
        """Test automatic worktree path generation."""
        logger.info("Testing worktree path generation...")

        path = get_worktree_path(self.test_wo_id, self.repo_root)
        # Worktrees are now created OUTSIDE the repo (Nivel A integration)
        expected = self.repo_root.parent / ".worktrees" / self.test_wo_id

        if path == expected.resolve():
            logger.info(f"✓ Worktree path: {path}")
            return True
        else:
            logger.error(f"✗ Path generation failed: expected {expected}, got {path}")
            return False

    def test_lock_creation(self) -> bool:
        """Test atomic lock creation."""
        logger.info("Testing lock creation...")

        running_dir = self.repo_root / "_ctx" / "jobs" / "running"
        running_dir.mkdir(parents=True, exist_ok=True)
        lock_path = running_dir / f"{self.test_wo_id}.lock"

        # Remove existing lock if any
        if lock_path.exists():
            lock_path.unlink()

        # Create lock
        if not create_lock(lock_path, self.test_wo_id):
            logger.error("✗ Lock creation failed")
            return False

        # Verify lock exists and contains metadata
        if not lock_path.exists():
            logger.error("✗ Lock file not created")
            return False

        content = lock_path.read_text()
        if "ctx_wo_take.py" in content and "PID:" in content:
            logger.info("✓ Lock created with metadata")
            logger.info(f"  Lock content:\n{content}")
            return True
        else:
            logger.error("✗ Lock missing metadata")
            return False

    def test_lock_age_detection(self) -> bool:
        """Test stale lock detection."""
        logger.info("Testing lock age detection...")

        running_dir = self.repo_root / "_ctx" / "jobs" / "running"
        lock_path = running_dir / f"{self.test_wo_id}.lock"

        # Fresh lock should not be stale
        if check_lock_age(lock_path, max_age_seconds=3600):
            logger.error("✗ Fresh lock detected as stale")
            return False

        logger.info("✓ Fresh lock not detected as stale")

        # Test with very short max age
        if not check_lock_age(lock_path, max_age_seconds=0):
            logger.error("✗ Old lock not detected as stale")
            return False

        logger.info("✓ Old lock correctly detected as stale")
        return True

    def test_worktree_creation(self) -> bool:
        """Test automatic worktree creation."""
        logger.info("Testing worktree creation...")

        try:
            # Create worktree with auto-generated branch and path
            branch, worktree_path = create_worktree(
                self.repo_root,
                self.test_wo_id,
                branch=None,  # Auto-generate
                worktree_path=None,  # Auto-generate
            )

            logger.info("✓ Worktree created:")
            logger.info(f"  Branch: {branch}")
            logger.info(f"  Path: {worktree_path}")

            # Verify worktree exists
            if not worktree_path.exists():
                logger.error("✗ Worktree directory not created")
                return False

            # Verify worktree is registered
            result = run_command(["git", "worktree", "list"], cwd=self.repo_root)
            if str(worktree_path) not in result.stdout:
                logger.error("✗ Worktree not registered with git")
                return False

            # Verify branch exists
            result = run_command(
                ["git", "rev-parse", "--verify", branch], cwd=self.repo_root, check=False
            )
            if result.returncode != 0:
                logger.error(f"✗ Branch {branch} not created")
                return False

            logger.info("✓ Worktree properly registered and branch created")
            return True

        except Exception as e:
            logger.error(f"✗ Worktree creation failed: {e}")
            return False

    def test_worktree_list(self) -> bool:
        """Test listing worktrees."""
        logger.info("Testing worktree listing...")

        try:
            worktrees = list_worktrees(self.repo_root)

            if not worktrees:
                logger.error("✗ No worktrees found")
                return False

            logger.info(f"✓ Found {len(worktrees)} worktree(s):")
            for wt in worktrees:
                logger.info(f"  - {wt.get('worktree', 'unknown')}")

            # Verify our test worktree is in the list
            test_path = str(get_worktree_path(self.test_wo_id, self.repo_root))
            found = any(test_path in wt.get("worktree", "") for wt in worktrees)

            if found:
                logger.info("✓ Test worktree found in list")
                return True
            else:
                logger.error("✗ Test worktree not found in list")
                return False

        except Exception as e:
            logger.error(f"✗ Worktree listing failed: {e}")
            return False

    def test_worktree_idempotency(self) -> bool:
        """Test that calling create_worktree twice is idempotent."""
        logger.info("Testing worktree creation idempotency...")

        try:
            # First creation should succeed
            branch1, path1 = create_worktree(
                self.repo_root,
                self.test_wo_id,
                branch=None,
                worktree_path=None,
            )

            # Second creation should detect existing worktree
            branch2, path2 = create_worktree(
                self.repo_root,
                self.test_wo_id,
                branch=None,
                worktree_path=None,
            )

            if branch1 == branch2 and path1 == path2:
                logger.info("✓ Idempotent: duplicate creation returns same values")
                return True
            else:
                logger.error("✗ Idempotency failed: different values returned")
                return False

        except Exception as e:
            logger.error(f"✗ Idempotency test failed: {e}")
            return False

    def run_all(self) -> dict:
        """Run all tests and return results."""
        results = {"setup": self.setup(), "tests": {}}

        if not results["setup"]:
            logger.error("Setup failed, skipping tests")
            return results

        tests = [
            ("branch_generation", self.test_branch_generation),
            ("worktree_path_generation", self.test_worktree_path_generation),
            ("lock_creation", self.test_lock_creation),
            ("lock_age_detection", self.test_lock_age_detection),
            ("worktree_creation", self.test_worktree_creation),
            ("worktree_list", self.test_worktree_list),
            ("worktree_idempotency", self.test_worktree_idempotency),
        ]

        for name, test_func in tests:
            try:
                results["tests"][name] = test_func()
            except Exception as e:
                logger.error(f"Test {name} raised exception: {e}")
                results["tests"][name] = False

        self.teardown()
        return results


def main():
    """Run WO orchestration tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test WO orchestration")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   WO Orchestration Test Suite")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    test = WOOrchestrationTest(repo_root)
    results = test.run_all()

    # Print summary
    print("\n" + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Test Results")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    total = len(results["tests"])
    passed = sum(1 for v in results["tests"].values() if v)

    for name, result in results["tests"].items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
