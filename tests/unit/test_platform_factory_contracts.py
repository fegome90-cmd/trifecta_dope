import pytest

from src.trifecta.platform.registry import RegistryFactory
from src.trifecta.platform.runtime_manager import RuntimeManagerFactory


def test_runtime_manager_factory_raises_clear_error_for_missing_daemon_impl() -> None:
    with pytest.raises(NotImplementedError, match="daemon runtime manager"):
        RuntimeManagerFactory.create("daemon")


def test_runtime_manager_factory_raises_clear_error_for_missing_embedded_impl() -> None:
    with pytest.raises(NotImplementedError, match="embedded runtime manager"):
        RuntimeManagerFactory.create("embedded")


def test_registry_factory_raises_clear_error_for_missing_memory_impl() -> None:
    with pytest.raises(NotImplementedError, match="memory registry"):
        RegistryFactory.create("memory")


def test_registry_factory_raises_clear_error_for_missing_sqlite_impl() -> None:
    with pytest.raises(NotImplementedError, match="sqlite registry"):
        RegistryFactory.create("sqlite")
