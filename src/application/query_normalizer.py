"""Query normalization and tokenization for search."""

import re
from typing import List


class QueryNormalizer:
    """Normalize and tokenize search queries."""
    
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
        q = re.sub(r'\s+', ' ', q)
        
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
        tokens = re.split(r'[\s\-_/\.]+', query)
        
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
