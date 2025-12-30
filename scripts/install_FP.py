import argparse
import subprocess
import sys
from pathlib import Path

# Import domain logic from Clean Architecture layer
from src.infrastructure.validators import ValidationResult, validate_segment_structure


def _legacy_validate_wrapper(path: Path) -> ValidationResult:
    """
    DEPRECATED: Legacy wrapper for backward compatibility.
    Use src.infrastructure.validators.validate_segment_structure directly.
    """
    return validate_segment_structure(path)


def _old_validate_logic(path: Path) -> ValidationResult:
    """
    OLD IMPLEMENTATION (DEPRECATED - moved to src/infrastructure/validators.py).
    Kept here for reference only.
    """
    errors = []
    
    if not path.exists():
        return ValidationResult(False, [f"Path not found: {path}"])

    # Obtenemos el "Context Name" del nombre de la carpeta
    context_name = path.name 
    
    # 1. skill.md suele ser el punto de entrada genérico (asumimos que este se mantiene fijo)
    # Si este también debe cambiar, avísame.
    if not (path / "skill.md").exists():
        errors.append("Missing generic entry point: skill.md")
    
    ctx_dir = path / "_ctx"
    if not ctx_dir.exists():
        errors.append("Missing directory: _ctx/")
        # Si no existe _ctx, no podemos validar lo de adentro, retornamos aquí.
        return ValidationResult(False, errors)

    # 2. Validación Dinámica (Interpolación de strings)
    # Definimos lo que esperamos encontrar
    expected_files = [
        f"agent_{context_name}.md",
        f"prime_{context_name}.md",
        f"session_{context_name}.md"
    ]

    for filename in expected_files:
        expected_path = ctx_dir / filename
        if not expected_path.exists():
            errors.append(f"Missing context file: _ctx/{filename}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)

# --- INFRAESTRUCTURA (IMPERATIVE SHELL) ---
# Aquí nos ensuciamos las manos con I/O, Subprocesos y Salida.

def run_sync_command(cli_root: Path, segment_path: Path) -> None:
    """Ejecuta el comando. Lanza excepción si falla (no sys.exit)."""
    cmd = ["uv", "run", "trifecta", "ctx", "sync", "--segment", str(segment_path)]
    
    # Usamos check=True para que lance CalledProcessError automáticamente si falla
    try:
        subprocess.run(
            cmd, 
            cwd=cli_root, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ Synced: {segment_path.name}")
    except subprocess.CalledProcessError as e:
        # Enriquecemos el error antes de lanzarlo arriba
        raise RuntimeError(f"❌ Sync failed for {segment_path.name}:\n{e.stderr}") from e

def main() -> int:
    parser = argparse.ArgumentParser(description="Trifecta Context Installer")
    parser.add_argument("--cli-root", type=str, default=".", help="Path to trifecta repo")
    parser.add_argument("--segment", type=str, action="append", required=True)
    args = parser.parse_args()

    cli_root = Path(args.cli_root).resolve()
    segments = [Path(s).resolve() for s in args.segment]

    print(f"🔧 CLI Root: {cli_root}")
    
    # FASE 1: Validación (Fail Fast en bloque)
    # Recolectamos TODOS los errores de TODOS los segmentos antes de ejecutar nada.
    all_errors = []
    valid_segments = []

    for seg in segments:
        result = validate_segment_structure(seg)
        if result.valid:
            valid_segments.append(seg)
        else:
            for err in result.errors:
                all_errors.append(f"[{seg.name}] {err}")

    if all_errors:
        print("\n🚫 Validation Errors Found:")
        print("\n".join(all_errors))
        return 1 # <--- Salimos con error
    
    # FASE 2: Ejecución
    print(f"\n🚀 Processing {len(valid_segments)} segments...")
    failed = False
    for seg in valid_segments:
        try:
            run_sync_command(cli_root, seg)
        except RuntimeError as e:
            print(e)
            failed = True
    
    if failed:
        return 1 # <--- Salimos con error
    
    print("\n✨ All done.")
    return 0 # <--- Éxito explícito

if __name__ == "__main__":
    sys.exit(main())