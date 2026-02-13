#!/usr/bin/env python3
"""
Shared I/O utilities for WO scripts.

Centralizes common file operations to avoid duplication.
"""
from pathlib import Path
from typing import Any
import yaml


def load_yaml(path: Path) -> dict[str, Any] | None:
    """Load YAML file with error handling.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content as dict, or None if file is empty
    """
    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write data to YAML file atomically.

    Args:
        path: Output file path
        data: Data to serialize as YAML
    """
    path.write_text(yaml.safe_dump(data, sort_keys=False))
