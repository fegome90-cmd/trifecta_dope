```python
# tests/unit/test_result_monad.py
import pytest
from src.domain.result import Ok, Err, Result

class TestResultMonad:
    def test_ok_is_success(self) -> None:
        result: Result[int, str] = Ok(42)
        assert result.is_ok() is True
        assert result.is_err() is False
        assert result.unwrap() == 42

    def test_err_is_failure(self) -> None:
        result: Result[int, str] = Err("Something failed")
        assert result.is_ok() is False
        assert result.is_err() is True
        assert result.unwrap_err() == "Something failed"

    def test_map_on_ok(self) -> None:
        result: Result[int, str] = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 20

    def test_map_on_err_does_nothing(self) -> None:
        result: Result[int, str] = Err("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_err() == "error"

    def test_and_then_chains_ok(self) -> None:
        result: Result[int, str] = Ok(5)
        chained = result.and_then(lambda x: Ok(x + 1) if x > 0 else Err("negative"))
        assert chained.unwrap() == 6

    def test_and_then_short_circuits_err(self) -> None:
        result: Result[int, str] = Err("first error")
        chained = result.and_then(lambda x: Ok(x + 1))
        assert chained.unwrap_err() == "first error"
```
