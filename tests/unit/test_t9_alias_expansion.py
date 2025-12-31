"""Tests for T9.A Alias Expansion functionality."""

import json
from pathlib import Path
import yaml  # type: ignore[import-untyped]

from src.infrastructure.alias_loader import AliasLoader
from src.application.query_normalizer import QueryNormalizer
from src.application.query_expander import QueryExpander


def test_alias_expansion_increases_hits(tmp_path: Path) -> None:
    """Verify that alias expansion increases search hits."""
    # Setup: Create a segment with context pack
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # Create context pack with a chunk containing "tree_sitter" but not "parser"
    context_pack = {
        "schema_version": 1,
        "chunks": [
            {
                "id": "test:chunk1",
                "title_path": ["test.py"],
                "text": "This module uses tree_sitter for parsing",
                "token_est": 10,
                "source_file": "test.py",
                "source_hash": "abc123"
            }
        ]
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(context_pack))
    
    # Create aliases.yaml: parser -> tree_sitter
    aliases = {
        "schema_version": 1,
        "aliases": {
            "parser": ["tree_sitter", "ast_parser"]
        }
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))
    
    # Load aliases and expand query
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    assert "parser" in loaded_aliases
    assert "tree_sitter" in loaded_aliases["parser"]
    
    # Expand query "parser"
    normalizer = QueryNormalizer()
    normalized = normalizer.normalize("parser")
    tokens = normalizer.tokenize(normalized)
    
    expander = QueryExpander(loaded_aliases)
    expanded = expander.expand(normalized, tokens)
    
    # Should have original + synonyms
    assert len(expanded) > 1
    assert ("parser", 1.0) in expanded
    assert any(term == "tree_sitter" and weight == 0.7 for term, weight in expanded)


def test_alias_expansion_caps_terms(tmp_path: Path) -> None:
    """Verify that alias expansion caps at MAX_EXTRA_TERMS (8)."""
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # Create aliases with >8 synonyms
    aliases = {
        "schema_version": 1,
        "aliases": {
            "test": [f"synonym{i}" for i in range(20)]  # 20 synonyms
        }
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))
    
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    expander = QueryExpander(loaded_aliases)
    expanded = expander.expand("test", ["test"])
    
    # Should have original (1) + max 8 extra = 9 total
    assert len(expanded) <= 9


def test_alias_expansion_dedupes_ids(tmp_path: Path) -> None:
    """Verify that alias expansion de-duplicates by chunk_id."""
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # Create context pack with one chunk matching multiple synonyms
    context_pack = {
        "schema_version": 1,
        "chunks": [
            {
                "id": "test:chunk1",
                "title_path": ["test.py"],
                "text": "authentication login session_guard",  # Contains all synonyms
                "token_est": 10,
                "source_file": "test.py",
                "source_hash": "abc123"
            }
        ]
    }
    (ctx_dir / "context_pack.json").write_text(json.dumps(context_pack))
    
    # Create aliases
    aliases = {
        "schema_version": 1,
        "aliases": {
            "auth": ["authentication", "login", "session_guard"]
        }
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))
    
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    expander = QueryExpander(loaded_aliases)
    expanded = expander.expand("auth", ["auth"])
    
    # All terms point to same chunk -> should de-dupe
    assert len(expanded) == 4  # auth + 3 synonyms


def test_telemetry_records_alias_fields(tmp_path: Path) -> None:
    """Verify that telemetry records alias expansion fields."""
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # Create aliases
    aliases = {
        "schema_version": 1,
        "aliases": {
            "parser": ["tree_sitter", "ast_parser"]
        }
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))
    
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    expander = QueryExpander(loaded_aliases)
    expanded = expander.expand("parser", ["parser"])
    
    metadata = expander.get_expansion_metadata(expanded)
    
    assert metadata["alias_expanded"] is True
    assert metadata["alias_terms_count"] == 2  # tree_sitter + ast_parser
    assert "parser" in metadata["alias_keys_used"]


def test_no_aliases_file_works_normally(tmp_path: Path) -> None:
    """Verify that search works normally without aliases.yaml."""
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # No aliases.yaml file
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    assert loaded_aliases == {}
    
    expander = QueryExpander(loaded_aliases)
    expanded = expander.expand("test", ["test"])
    
    # Should only have original query
    assert len(expanded) == 1
    assert expanded[0] == ("test", 1.0)


def test_alias_file_validation(tmp_path: Path) -> None:
    """Verify that alias file validation enforces limits."""
    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)
    
    # Create aliases exceeding MAX_KEYS (200)
    aliases_dict = {f"key{i}": [f"syn{i}"] for i in range(250)}
    aliases = {
        "schema_version": 1,
        "aliases": aliases_dict
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases))
    
    loader = AliasLoader(segment)
    loaded_aliases = loader.load()
    
    # Should cap at MAX_KEYS (200)
    assert len(loaded_aliases) <= AliasLoader.MAX_KEYS
    
    # Test MAX_SYNONYMS_PER_KEY
    aliases_long = {
        "schema_version": 1,
        "aliases": {
            "test": [f"synonym{i}" for i in range(30)]  # 30 synonyms
        }
    }
    (ctx_dir / "aliases.yaml").write_text(yaml.dump(aliases_long))
    
    loader2 = AliasLoader(segment)
    loaded_aliases2 = loader2.load()
    
    # Should cap at MAX_SYNONYMS_PER_KEY (20)
    assert len(loaded_aliases2["test"]) <= AliasLoader.MAX_SYNONYMS_PER_KEY
