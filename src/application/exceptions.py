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
