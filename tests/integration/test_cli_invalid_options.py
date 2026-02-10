"""Tests de regresión para opciones inválidas en CLI.

Dataset de baseline capturado en WO-0022.
Valida que el CLI maneje correctamente flags inválidos.
"""

import subprocess
import pytest


INVALID_OPTIONS_DATASET = [
    {
        "id": "load_dry_run",
        "command": [
            "uv",
            "run",
            "trifecta",
            "load",
            "--segment",
            ".",
            "--task",
            "test",
            "--dry-run",
        ],
        "invalid_flag": "--dry-run",
        "expected_in_output": ["No such option", "--dry-run"],
        "suggested_help": "trifecta load --help",
    },
    {
        "id": "plan_max_steps",
        "command": [
            "uv",
            "run",
            "trifecta",
            "ctx",
            "plan",
            "--segment",
            ".",
            "--task",
            "test",
            "--max-steps",
            "5",
        ],
        "invalid_flag": "--max-steps",
        "expected_in_output": ["No such option", "--max-steps"],
        "suggested_help": "trifecta ctx plan --help",
    },
]


@pytest.mark.parametrize("test_case", INVALID_OPTIONS_DATASET, ids=lambda x: x["id"])
def test_invalid_option_error_message(test_case):
    """Valida que flags inválidos generen mensajes de error apropiados."""
    result = subprocess.run(
        test_case["command"],
        capture_output=True,
        text=True,
    )

    # Debe fallar con código de error
    assert result.returncode != 0, f"Comando {test_case['id']} debería fallar"

    # Debe mencionar el flag inválido
    combined_output = result.stdout + result.stderr
    for expected in test_case["expected_in_output"]:
        assert expected in combined_output, (
            f"Output debe contener '{expected}'\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


@pytest.mark.parametrize("test_case", INVALID_OPTIONS_DATASET, ids=lambda x: x["id"])
def test_invalid_option_suggests_help(test_case):
    """Valida que el error sugiera consultar --help."""
    result = subprocess.run(
        test_case["command"],
        capture_output=True,
        text=True,
    )

    combined_output = result.stdout + result.stderr

    # Debe sugerir usar --help
    assert "--help" in combined_output, (
        f"Error debería sugerir --help\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Debe sugerir el comando específico para help
    assert (
        test_case["suggested_help"] in combined_output
        or "Para ver opciones disponibles" in combined_output
    ), f"Error debería sugerir: {test_case['suggested_help']}"


@pytest.mark.parametrize("test_case", INVALID_OPTIONS_DATASET, ids=lambda x: x["id"])
def test_invalid_option_includes_example(test_case):
    """Valida que el error incluya ejemplo de uso correcto."""
    result = subprocess.run(
        test_case["command"],
        capture_output=True,
        text=True,
    )

    combined_output = result.stdout + result.stderr

    # Debe incluir sección de ejemplo
    assert "Ejemplo de uso:" in combined_output, (
        f"Error debería incluir ejemplo de uso\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Debe incluir un comando de ejemplo con uv run
    assert "uv run trifecta" in combined_output, (
        f"Ejemplo debería usar formato uv run trifecta\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize("test_case", INVALID_OPTIONS_DATASET, ids=lambda x: x["id"])
def test_invalid_option_exit_code(test_case):
    """Valida que el código de salida sea 2 (uso incorrecto)."""
    result = subprocess.run(
        test_case["command"],
        capture_output=True,
        text=True,
    )

    # Código 2 es el estándar para errores de uso (CLI misuse)
    assert result.returncode == 2, (
        f"Código de salida debería ser 2, no {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
