"""Application-layer exceptions for Trifecta use cases."""

from pathlib import Path


class PrimeFileNotFoundError(FileNotFoundError):
    """Raised when the expected prime file is missing for a segment.

    This exception is used to distinguish prime file errors from other
    FileNotFoundError cases, enabling type-based error classification
    in the CLI handler.
    """

    def __init__(self, expected_path: Path, segment_id: str, message: str | None = None):
        """Initialize with path and segment information.

        Args:
            expected_path: The path where the prime file was expected
            segment_id: The normalized segment identifier
            message: Optional custom message (defaults to standard format)
        """
        self.expected_path = expected_path
        self.segment_id = segment_id

        if message is None:
            message = (
                f"Expected prime file not found: _ctx/prime_{segment_id}.md. "
                f"Segment ID derived from directory name: '{expected_path.parent.parent.name}' -> '{segment_id}'"
            )

        super().__init__(message)


class InvalidSegmentPathError(FileNotFoundError):
    """Raised when --segment path cannot be resolved to an existing directory."""

    def __init__(self, segment_input: str, resolved_path: Path, message: str | None = None):
        self.segment_input = segment_input
        self.resolved_path = resolved_path
        if message is None:
            message = (
                f"Invalid segment path: input='{segment_input}' "
                f"resolved='{resolved_path}' (path does not exist or is not a directory)"
            )
        super().__init__(message)


class InvalidConfigScopeError(ValueError):
    """Raised when trifecta_config.json repo_root does not match resolved segment root."""

    def __init__(self, config_repo_root: Path, resolved_segment_root: Path, message: str | None = None):
        self.config_repo_root = config_repo_root
        self.resolved_segment_root = resolved_segment_root
        if message is None:
            message = (
                f"Invalid config scope: repo_root='{config_repo_root}' "
                f"does not match resolved segment root='{resolved_segment_root}'"
            )
        super().__init__(message)
