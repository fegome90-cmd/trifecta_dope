"""
Tests for Result Monad (FP Error Handling).

TDD Phase: RED -> GREEN
"""


import pytest

from src.domain.result import Err, Ok


class TestResultMonad:
    """Test suite for Ok and Err Result types."""

    def test_ok_is_success(self) -> None:
        result = Ok(42)
        assert result.is_ok() is True
        assert result.is_err() is False
        assert result.unwrap() == 42

    def test_err_is_failure(self) -> None:
        result = Err("Something failed")
        assert result.is_ok() is False
        assert result.is_err() is True
        assert result.unwrap_err() == "Something failed"

    def test_map_on_ok(self) -> None:
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 20

    def test_map_on_err_does_nothing(self) -> None:
        result: Err[str] = Err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_err() == "error"

    def test_and_then_chains_ok(self) -> None:
        result = Ok(5)
        chained = result.and_then(lambda x: Ok(x + 1) if x > 0 else Err("negative"))
        assert chained.unwrap() == 6

    def test_and_then_short_circuits_err(self) -> None:
        result: Err[str] = Err("first error")
        chained = result.and_then(lambda x: Ok(x + 1))
        assert chained.unwrap_err() == "first error"

    def test_unwrap_on_err_raises(self) -> None:
        result: Err[str] = Err("error")
        with pytest.raises(ValueError):
            result.unwrap()

    def test_unwrap_err_on_ok_raises(self) -> None:
        result = Ok(42)
        with pytest.raises(ValueError):
            result.unwrap_err()

    def test_ok_is_frozen(self) -> None:
        result = Ok(42)
        with pytest.raises(AttributeError):
            result.value = 100  # type: ignore[misc]

    def test_err_is_frozen(self) -> None:
        result: Err[str] = Err("error")
        with pytest.raises(AttributeError):
            result.error = "new"  # type: ignore[misc]
