"""
Sanitizer Service - Centralized PII and path redaction policy.

Ensures that sensitive information (absolute paths, secrets, tokens) 
never leaves the trust boundary via telemetry or MCP responses.
"""

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Union


class Sanitizer:
    """
    Authoritative sanitizer for the Trifecta ecosystem.
    
    Implements Law IV: ZERO TRUST PATHS.
    """

    # Patterns for absolute paths that should be redacted
    _PATH_PATTERNS = [
        r"/(?:Users|home|private/var|mnt/[cdCD])/[^\s]+", # POSIX/WSL (greedy)
        r"[a-zA-Z]:\\(?:Users|users)\\[^\s]+",          # Windows (greedy)
        r"file:///(?:Users|home|private/var)/[^\s]+",  # URIs (greedy)
    ]
    
    # Common keys that likely contain paths in dictionaries
    _PATH_KEYS = {"segment", "cwd", "path", "root", "repo_root", "file", "uri", "source_path"}
    
    # Common keys that likely contain secrets
    _SECRET_KEYS = {"token", "secret", "password", "api_key", "apikey", "passwd", "key"}

    # Patterns for secrets/tokens
    _SECRET_PATTERNS = [
        (r"(api[_-]?key|apikey|token|secret|password|passwd)\s*[=:]\s*['\"]?[A-Za-z0-9_+\-/=@%+-]{20,}", "***REDACTED***"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***"), # Email
    ]

    def __init__(self, redact_paths: bool = True, redact_secrets: bool = True):
        self._redact_paths = redact_paths
        self._redact_secrets = redact_secrets
        
        # Compile regex for speed
        self._path_re = re.compile("|".join(self._PATH_PATTERNS))

    def redact(self, text: str) -> str:
        """Redact PII from a raw string."""
        if not text:
            return text

        result = text
        
        # 1. Path Redaction
        if self._redact_paths:
            result = self._path_re.sub("<ABS_PATH_REDACTED>", result)

        # 2. Secret Redaction
        if self._redact_secrets:
            for pattern, replacement in self._SECRET_PATTERNS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary."""
        if os.environ.get("TRIFECTA_PII") == "allow":
            return data

        sanitized = {}
        for k, v in data.items():
            if isinstance(v, str):
                # If key is a known secret key, redact completely
                if k.lower() in self._SECRET_KEYS:
                    sanitized[k] = "***REDACTED***"
                else:
                    sanitized[k] = self.redact(v)
            elif isinstance(v, dict):
                sanitized[k] = self.sanitize_dict(v)
            elif isinstance(v, list):
                sanitized[k] = [self.sanitize_dict(item) if isinstance(item, dict) else (self.redact(item) if isinstance(item, str) else item) for item in v]
            else:
                sanitized[k] = v
        return sanitized

    @staticmethod
    def get_repo_relative_path(root: Path, target: Path) -> str:
        """Convert absolute path to repo-relative path string."""
        try:
            return str(target.relative_to(root))
        except ValueError:
            # External file - hash the full path for privacy
            import hashlib
            path_hash = hashlib.sha256(str(target).encode()).hexdigest()[:8]
            return f"external/{path_hash}-{target.name}"
