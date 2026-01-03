"""Unit tests for parse_chunk_id helper."""

from src.application.context_service import parse_chunk_id


def test_parse_valid_prime_id():
    """Test parsing valid prime chunk ID."""
    kind, rest = parse_chunk_id("prime:abcd1234")
    assert kind == "prime"
    assert rest == "abcd1234"


def test_parse_valid_skill_id():
    """Test parsing valid skill chunk ID."""
    kind, rest = parse_chunk_id("skill:xyz789")
    assert kind == "skill"
    assert rest == "xyz789"


def test_parse_valid_agent_id():
    """Test parsing valid agent chunk ID."""
    kind, rest = parse_chunk_id("agent:hash123")
    assert kind == "agent"
    assert rest == "hash123"


def test_parse_invalid_no_colon():
    """Test parsing invalid ID without colon."""
    kind, rest = parse_chunk_id("weird_id_format")
    assert kind == "unknown"
    assert rest == "weird_id_format"


def test_parse_multiple_colons():
    """Test parsing ID with multiple colons (split on first only)."""
    kind, rest = parse_chunk_id("prime:foo:bar:baz")
    assert kind == "prime"
    assert rest == "foo:bar:baz"


def test_parse_empty_string():
    """Test parsing empty string."""
    kind, rest = parse_chunk_id("")
    assert kind == "unknown"
    assert rest == ""


def test_parse_case_sensitive():
    """Test that parser normalizes kind to lowercase."""
    kind, rest = parse_chunk_id("Prime:abc")
    assert kind == "prime"  # Normalized to lowercase
    assert rest == "abc"
