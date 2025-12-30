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
    
    (seg / "skill.md").touch() # Archivo estático
    
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
    (ctx / "agent_marketing.md").touch()   # <--- Nombre incorrecto
    (ctx / "prime_marketing.md").touch()
    (ctx / "session_marketing.md").touch()

    # 2. Act
    result = validate_segment_structure(seg)

    # 3. Assert
    assert result.valid is False
    # Verificamos que el error mencione el archivo que esperábamos ver
    assert any("agent_ventas.md" in e for e in result.errors)