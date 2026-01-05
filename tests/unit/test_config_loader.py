"""Unit tests for ConfigLoader with auditable missing_config markers."""

from src.infrastructure.config_loader import ConfigLoader


def test_load_anchors_existing(tmp_path):
    """Should load anchors.yaml when it exists without _missing_config marker."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("""
anchors:
  strong:
    files:
      - "agent.md"
      - "prime.md"
  weak:
    intent_terms:
      - "doc"
      - "docs"
""")

    result = ConfigLoader.load_anchors(tmp_path)

    assert "anchors" in result
    assert "agent.md" in result["anchors"]["strong"]["files"]
    assert "prime.md" in result["anchors"]["strong"]["files"]
    assert "doc" in result["anchors"]["weak"]["intent_terms"]
    assert "_missing_config" not in result


def test_load_anchors_missing(tmp_path):
    """Should return dict with _missing_config marker when anchors.yaml missing."""
    result = ConfigLoader.load_anchors(tmp_path)

    assert result == {"_missing_config": True, "anchors": {}}


def test_load_anchors_invalid_yaml(tmp_path):
    """Should return dict with _missing_config marker when anchors.yaml is invalid."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    anchors_file = configs_dir / "anchors.yaml"
    anchors_file.write_text("invalid: yaml: content: [")

    result = ConfigLoader.load_anchors(tmp_path)

    assert result == {"_missing_config": True, "anchors": {}}


def test_load_aliases_existing(tmp_path):
    """Should load aliases.yaml when it exists without _missing_config marker."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    aliases_file = configs_dir / "aliases.yaml"
    aliases_file.write_text("""
aliases:
  - trigger: "persistencia de sesión"
    strong:
      - "session.md"
    weak: []
    append_mode: true
""")

    result = ConfigLoader.load_linter_aliases(tmp_path)

    assert "aliases" in result
    assert len(result["aliases"]) == 1
    assert result["aliases"][0]["trigger"] == "persistencia de sesión"
    assert "_missing_config" not in result


def test_load_aliases_missing(tmp_path):
    """Should return dict with _missing_config marker when aliases.yaml missing."""
    result = ConfigLoader.load_linter_aliases(tmp_path)

    assert result == {"_missing_config": True, "aliases": []}


def test_load_aliases_invalid_yaml(tmp_path):
    """Should return dict with _missing_config marker when aliases.yaml is invalid."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    aliases_file = configs_dir / "aliases.yaml"
    aliases_file.write_text("{ invalid yaml }")

    result = ConfigLoader.load_linter_aliases(tmp_path)

    assert result == {"_missing_config": True, "aliases": []}
