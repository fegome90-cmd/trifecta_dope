"""Query expansion with alias support and weighting."""

from typing import Dict, List, Tuple, Set


class QueryExpander:
    """Expand queries using aliases with weighted terms."""
    
    MAX_EXTRA_TERMS = 8
    ORIGINAL_WEIGHT = 1.0
    ALIAS_WEIGHT = 0.7
    
    def __init__(self, aliases: Dict[str, List[str]]):
        """Initialize expander with aliases.
        
        Args:
            aliases: Dict mapping alias keys to synonym lists
        """
        self.aliases = aliases
    
    def expand(self, query: str, tokens: List[str]) -> List[Tuple[str, float]]:
        """Expand query using aliases with weights.
        
        Args:
            query: Normalized query string
            tokens: Query tokens
            
        Returns:
            List of (term, weight) tuples, capped at MAX_EXTRA_TERMS
        """
        if not self.aliases:
            # No aliases -> return original query only
            return [(query, self.ORIGINAL_WEIGHT)]
        
        # Start with original query
        terms: List[Tuple[str, float]] = [(query, self.ORIGINAL_WEIGHT)]
        
        # Track added terms to avoid duplicates
        added_terms: Set[str] = {query}
        
        # Check if full query matches an alias key
        if query in self.aliases:
            for synonym in self.aliases[query]:
                if synonym not in added_terms and len(added_terms) - 1 < self.MAX_EXTRA_TERMS:
                    terms.append((synonym, self.ALIAS_WEIGHT))
                    added_terms.add(synonym)
        
        # Check each token
        for token in tokens:
            if token in self.aliases:
                for synonym in self.aliases[token]:
                    if synonym not in added_terms and len(added_terms) - 1 < self.MAX_EXTRA_TERMS:
                        terms.append((synonym, self.ALIAS_WEIGHT))
                        added_terms.add(synonym)
            
            # Stop if we've hit the cap
            if len(added_terms) - 1 >= self.MAX_EXTRA_TERMS:
                break
        
        return terms
    
    def get_expansion_metadata(self, terms: List[Tuple[str, float]]) -> Dict:
        """Get metadata about the expansion for telemetry.
        
        Args:
            terms: List of (term, weight) tuples from expand()
            
        Returns:
            Dict with expansion metadata
        """
        alias_terms = [t for t, w in terms if w == self.ALIAS_WEIGHT]
        
        # Find which alias keys were used
        keys_used = []
        for key, synonyms in self.aliases.items():
            for term in alias_terms:
                if term in synonyms:
                    keys_used.append(key)
                    break
        
        return {
            "alias_expanded": len(alias_terms) > 0,
            "alias_terms_count": len(alias_terms),
            "alias_keys_used": keys_used[:5]  # Cap at 5 for telemetry
        }
