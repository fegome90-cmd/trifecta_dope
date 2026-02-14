"""Query normalization and tokenization for search."""

import re
from typing import List, Tuple

from src.domain.result import Ok, Err


class QueryValidationError(Exception):
    """Raised when query fails validation."""

    pass


class QueryNormalizer:
    """Normalize and tokenize search queries."""

    @staticmethod
    def validate(query: str) -> Tuple[bool, str]:
        """Validate query before normalization.

        B2 Intervention: Reject empty or whitespace-only queries early
        to prevent unnecessary zero-hit searches.

        Args:
            query: Raw query string

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if query passes validation
            - error_message: Empty string if valid, description if invalid
        """
        if query is None:
            return False, "Query cannot be None"

        if not isinstance(query, str):
            return False, "Query must be a string"

        stripped = query.strip()

        if not stripped:
            return False, "Query cannot be empty or whitespace-only"

        if len(stripped) < 2:
            return False, "Query must be at least 2 characters"

        return True, ""

    @staticmethod
    def normalize(query: str) -> str:
        """Normalize query: lowercase, strip, collapse whitespace.

        Args:
            query: Raw query string

        Returns:
            Normalized query string
        """
        if not query:
            return ""

        # Lowercase
        q = query.lower()

        # Strip leading/trailing whitespace
        q = q.strip()

        # Collapse multiple whitespace to single space
        q = re.sub(r"\s+", " ", q)

        return q

    @staticmethod
    def tokenize(query: str) -> List[str]:
        """Tokenize query by splitting on separators and deduping.

        Splits on: whitespace, -, _, /, .
        Removes: tokens of length 1
        Deduplicates while preserving order

        Args:
            query: Normalized query string

        Returns:
            List of deduplicated tokens (len > 1)
        """
        if not query:
            return []

        # Split by separators: whitespace, -, _, /, .
        tokens = re.split(r"[\s\-_/\.]+", query)

        # Remove empty strings and tokens of length 1
        tokens = [t for t in tokens if len(t) > 1]

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                deduped.append(token)

        return deduped
