"""Obsidian configuration management.

This module handles loading and saving Obsidian integration configuration,
following the Trifecta configuration precedence pattern (P5 compliant).

Precedence order (highest to lowest):
1. CLI flags (e.g., --vault-path)
2. Environment variables (TRIFECTA_OBSIDIAN_*)
3. Config file (~/.config/trifecta/obsidian.yaml)
4. Default values

Following Trifecta Clean Architecture:
- Infrastructure layer: handles file I/O and env var access
- Uses domain models from src.domain.obsidian_models
- P5: Explicit precedence table documented in docstring
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from src.domain.obsidian_models import ObsidianConfig


class ObsidianConfigManager:
    """Manage Obsidian configuration with precedence support.

    Precedence Table (P5 compliant):
    +------------------------+------------------------+----------+
    | Source                 | Example                | Priority |
    +------------------------+------------------------+----------+
    | CLI Flag               | --vault-path ~/Vault   | 1 (high) |
    | Environment Variable   | TRIFECTA_OBSIDIAN_VAULT| 2        |
    | Config File            | ~/.config/.../obsidian.yaml| 3   |
    | Default                | ~/Obsidian/DefaultVault| 4 (low) |
    +------------------------+------------------------+----------+

    Usage:
        manager = ObsidianConfigManager()
        config = manager.load()

        # Override with CLI flag
        config = manager.load(vault_path=Path("~/CustomVault"))

        # Save to config file
        manager.save(config)
    """

    DEFAULT_CONFIG_PATH: Path = Path.home() / ".config" / "trifecta" / "obsidian.yaml"
    DEFAULT_VAULT_PATH: Path = Path.home() / "Obsidian" / "TrifectaFindings"

    ENV_PREFIX: str = "TRIFECTA_OBSIDIAN_"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_path: Path to config file (defaults to DEFAULT_CONFIG_PATH)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH

    def load(
        self,
        vault_path: Optional[Path] = None,
        min_priority: Optional[str] = None,
    ) -> ObsidianConfig:
        """Load configuration with precedence.

        Precedence: vault_path arg > env var > config file > default

        Args:
            vault_path: Override vault path from CLI flag
            min_priority: Override min priority from CLI flag

        Returns:
            ObsidianConfig instance
        """
        # Start with defaults
        config = self._load_defaults()

        # Load from config file (if exists)
        if self.config_path.exists():
            config = self._merge_file_config(config)

        # Load from environment variables
        config = self._merge_env_config(config)

        # Apply CLI flag overrides (highest priority)
        if vault_path is not None:
            config = ObsidianConfig(
                vault_path=vault_path.expanduser().resolve(),
                default_segment=config.default_segment,
                min_priority=config.min_priority,
                note_folder=config.note_folder,
                auto_link=config.auto_link,
                date_format=config.date_format,
            )

        if min_priority is not None:
            # Validate priority value
            valid = {"P0", "P1", "P2", "P3", "P4", "P5"}
            if min_priority not in valid:
                raise ValueError(
                    f"Invalid min_priority: {min_priority}. Must be one of {valid}"
                )

            config = ObsidianConfig(
                vault_path=config.vault_path,
                default_segment=config.default_segment,
                min_priority=min_priority,  # type: ignore
                note_folder=config.note_folder,
                auto_link=config.auto_link,
                date_format=config.date_format,
            )

        return config

    def _load_defaults(self) -> ObsidianConfig:
        """Load default configuration."""
        return ObsidianConfig(
            vault_path=self.DEFAULT_VAULT_PATH,
            min_priority="P5",
            note_folder="Trifecta Findings",
            auto_link=True,
            date_format="%Y-%m-%d",
        )

    def _merge_file_config(self, config: ObsidianConfig) -> ObsidianConfig:
        """Merge configuration from file (lower priority than env/CLI)."""
        with open(self.config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        vault = data.get("vault_path", config.vault_path)
        if isinstance(vault, str):
            vault = Path(vault)

        return ObsidianConfig(
            vault_path=vault.expanduser().resolve(),
            default_segment=data.get("default_segment", config.default_segment),
            min_priority=data.get("min_priority", config.min_priority),
            note_folder=data.get("note_folder", config.note_folder),
            auto_link=data.get("auto_link", config.auto_link),
            date_format=data.get("date_format", config.date_format),
        )

    def _merge_env_config(self, config: ObsidianConfig) -> ObsidianConfig:
        """Merge configuration from environment variables (higher priority than file)."""
        # TRIFECTA_OBSIDIAN_VAULT
        if env_vault := os.environ.get(f"{self.ENV_PREFIX}VAULT"):
            vault_path = Path(env_vault).expanduser().resolve()
        else:
            vault_path = config.vault_path

        # TRIFECTA_OBSIDIAN_MIN_PRIORITY
        env_priority = os.environ.get(f"{self.ENV_PREFIX}MIN_PRIORITY")
        if env_priority:
            valid = {"P0", "P1", "P2", "P3", "P4", "P5"}
            if env_priority not in valid:
                raise ValueError(
                    f"Invalid TRIFECTA_OBSIDIAN_MIN_PRIORITY: {env_priority}. "
                    f"Must be one of {valid}"
                )
            min_priority = env_priority  # type: ignore
        else:
            min_priority = config.min_priority

        # TRIFECTA_OBSIDIAN_FOLDER
        note_folder = os.environ.get(
            f"{self.ENV_PREFIX}FOLDER", config.note_folder
        )

        # TRIFECTA_OBSIDIAN_AUTO_LINK
        auto_link_str = os.environ.get(f"{self.ENV_PREFIX}AUTO_LINK", "")
        if auto_link_str:
            auto_link = auto_link_str.lower() in ("true", "1", "yes", "on")
        else:
            auto_link = config.auto_link

        return ObsidianConfig(
            vault_path=vault_path,
            default_segment=config.default_segment,
            min_priority=min_priority,
            note_folder=note_folder,
            auto_link=auto_link,
            date_format=config.date_format,
        )

    def save(self, config: ObsidianConfig) -> None:
        """Save configuration to file.

        Creates parent directories if needed.

        Args:
            config: Configuration to save
        """
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        data = {
            "vault_path": str(config.vault_path),
            "default_segment": config.default_segment,
            "min_priority": config.min_priority,
            "note_folder": config.note_folder,
            "auto_link": config.auto_link,
            "date_format": config.date_format,
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_vault_path(self) -> Path:
        """Get vault path from config or env var.

        Convenience method that uses full precedence.

        Returns:
            Absolute path to Obsidian vault
        """
        config = self.load()
        return config.vault_path

    def show(self) -> str:
        """Show current configuration as formatted string.

        Returns:
            Multi-line string showing current config
        """
        config = self.load()

        lines = [
            "Obsidian Configuration:",
            f"  Vault path: {config.vault_path}",
            f"  Min priority: {config.min_priority}",
            f"  Note folder: {config.note_folder}",
            f"  Auto-link: {config.auto_link}",
            f"  Date format: {config.date_format}",
            f"  Config file: {self.config_path}",
            "",
            "Precedence (highest to lowest):",
            "  1. CLI flags (--vault-path, --min-priority)",
            "  2. Environment variables (TRIFECTA_OBSIDIAN_*)",
            "  3. Config file (~/.config/trifecta/obsidian.yaml)",
            "  4. Default values",
        ]

        return "\n".join(lines)

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate current configuration.

        Checks:
        - Vault path exists
        - Vault path is writable
        - Findings directory can be created

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            config = self.load()

            # Check vault exists
            if not config.vault_path.exists():
                return False, f"Vault path does not exist: {config.vault_path}"

            # Check vault is a directory
            if not config.vault_path.is_dir():
                return False, f"Vault path is not a directory: {config.vault_path}"

            # Check vault is writable
            if not os.access(config.vault_path, os.W_OK):
                return False, f"Vault path is not writable: {config.vault_path}"

            # Check findings directory can be created
            findings_dir = config.findings_dir
            if findings_dir.exists():
                if not findings_dir.is_dir():
                    return False, f"Findings path exists but is not a directory: {findings_dir}"
            else:
                # Try to create it
                try:
                    findings_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    return False, f"Cannot create findings directory: {e}"

            return True, None

        except Exception as e:
            return False, f"Configuration error: {e}"
