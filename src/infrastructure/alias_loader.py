"""Alias loader for query expansion.

Loads and validates aliases.yaml files from segment directories.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml  # type: ignore[import-untyped]


class AliasLoader:
    """Load and validate alias files for query expansion."""
    
    MAX_KEYS = 200
    MAX_SYNONYMS_PER_KEY = 20
    
    def __init__(self, segment_path: Path):
        self.segment_path = segment_path
        self.aliases_path = segment_path / "_ctx" / "aliases.yaml"
    
    def load(self) -> Dict[str, List[str]]:
        """Load aliases from YAML file.
        
        Returns:
            Dict mapping alias keys to lists of synonyms.
            Empty dict if file doesn't exist or is invalid.
        """
        if not self.aliases_path.exists():
            return {}
        
        try:
            with open(self.aliases_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, dict):
                return {}
            
            # Validate schema version
            schema_version = data.get('schema_version')
            if schema_version != 1:
                return {}
            
            # Extract and validate aliases
            aliases = data.get('aliases', {})
            if not isinstance(aliases, dict):
                return {}
            
            # Validate and enforce limits
            validated = {}
            for key, synonyms in aliases.items():
                if not isinstance(key, str) or not isinstance(synonyms, list):
                    continue
                
                # Validate all synonyms are strings
                valid_synonyms = [s for s in synonyms if isinstance(s, str)]
                
                # Enforce max synonyms per key
                if len(valid_synonyms) > self.MAX_SYNONYMS_PER_KEY:
                    valid_synonyms = valid_synonyms[:self.MAX_SYNONYMS_PER_KEY]
                
                if valid_synonyms:
                    validated[key.lower()] = [s.lower() for s in valid_synonyms]
                
                # Enforce max keys
                if len(validated) >= self.MAX_KEYS:
                    break
            
            return validated
            
        except Exception:
            # Any error in loading/parsing -> return empty dict (fail safe)
            return {}
