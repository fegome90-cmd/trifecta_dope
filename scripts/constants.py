#!/usr/bin/env python3
"""
Shared constants for WO scripts.

Centralizes magic numbers and timeout values for better maintainability.
"""

# Timeouts (in seconds)
TEST_TIMEOUT = 300      # 5 minutes for test execution
LINT_TIMEOUT = 60       # 1 minute for linting
GIT_TIMEOUT = 30         # 30 seconds for git operations
DEFAULT_LOCK_TTL = 3600  # 1 hour for lock staleness

# Artifact file names (immutable tuple - use tuple() for iteration safety)
REQUIRED_ARTIFACTS = ("tests.log", "lint.log", "diff.patch", "handoff.md", "verdict.json")

# WO state transitions
WO_STATE_PENDING = "pending"
WO_STATE_RUNNING = "running"
WO_STATE_DONE = "done"
WO_STATE_FAILED = "failed"
