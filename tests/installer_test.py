from pathlib import Path

from src.infrastructure.validators import validate_segment_structure


# 1. Añadimos ': Path' para que el linter sepa qué es tmp_path
# 2. Añadimos '-> None' porque los tests no retornan nada
def test_valid_segment_dynamic_naming(tmp_path: Path) -> None:
    """
    Escenario: Carpeta llamada 'marketing'.
    Archivos esperados: agent_marketing.md, prime_marketing.md, etc.
    """
    # 1. Arrange
    segment_name = "marketing"
    seg = tmp_path / segment_name
    seg.mkdir()

    (seg / "skill.md").touch()  # Archivo estático

    ctx = seg / "_ctx"
    ctx.mkdir()

    # Creamos los archivos respetando la convención de nombres
    (ctx / f"agent_{segment_name}.md").touch()
    (ctx / f"prime_{segment_name}.md").touch()
    (ctx / f"session_{segment_name}.md").touch()

    # 2. Act
    result = validate_segment_structure(seg)

    # 3. Assert
    assert result.valid is True
    assert result.errors == []


def test_invalid_segment_name_mismatch(tmp_path: Path) -> None:
    """
    Escenario: Carpeta llamada 'ventas', pero archivos llamados 'marketing'.
    Resultado: Debe fallar porque no coinciden.
    """
    # 1. Arrange
    seg = tmp_path / "ventas"  # <--- Nombre de la carpeta
    seg.mkdir()
    (seg / "skill.md").touch()
    ctx = seg / "_ctx"
    ctx.mkdir()

    # Creamos archivos con el nombre INCORRECTO
    (ctx / "agent_marketing.md").touch()  # <--- Nombre incorrecto
    (ctx / "prime_marketing.md").touch()
    (ctx / "session_marketing.md").touch()

    # 2. Act
    result = validate_segment_structure(seg)

    # 3. Assert
    assert result.valid is False
    # Verificamos que el error mencione el archivo que esperábamos ver
    assert any("agent_ventas.md" in e for e in result.errors)


def test_install_fp_warns_on_legacy_names(tmp_path: Path) -> None:
    # Create fake CLI root with pyproject.toml
    cli_root = tmp_path / "cli"
    cli_root.mkdir()
    (cli_root / "pyproject.toml").write_text("[project]\nname='trifecta'\n")

    # Create legacy segment
    seg = tmp_path / "legacyseg"
    seg.mkdir()
    (seg / "skill.md").touch()
    ctx = seg / "_ctx"
    ctx.mkdir()
    (ctx / "agent.md").touch()
    (ctx / "prime.md").touch()
    (ctx / "session.md").touch()

    from scripts.install_FP import _format_legacy_warning

    warning = _format_legacy_warning(seg, ["agent.md", "prime.md", "session.md"])
    assert "legacy" in warning.lower()
    assert "agent.md" in warning
