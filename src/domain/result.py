"""
Functional Result Monad for Railway Oriented Programming.

Inspired by Rust's Result<T, E> and Haskell's Either.
Pure domain module - no external dependencies.

Author: Trifecta Team
Date: 2025-12-31
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, TypeAlias, TypeVar

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Mapped type


@dataclass(frozen=True)
class Ok(Generic[T]):
    """Represents a successful result."""

    value: T

    def is_ok(self) -> bool:
        """Return True if this is an Ok result."""
        return True

    def is_err(self) -> bool:
        """Return False since this is not an Err."""
        return False

    def unwrap(self) -> T:
        """Extract the success value. For tests/ergonomics only."""
        return self.value

    def unwrap_err(self) -> None:
        """Raise ValueError since this is not an Err. For tests only."""
        raise ValueError("Called unwrap_err on Ok")

    def map(self, fn: Callable[[T], U]) -> Ok[U]:
        """Apply function to success value, returning new Ok."""
        return Ok(fn(self.value))

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Chain with another Result-returning function."""
        return fn(self.value)


@dataclass(frozen=True)
class Err(Generic[E]):
    """Represents a failed result."""

    error: E

    def is_ok(self) -> bool:
        """Return False since this is not an Ok."""
        return False

    def is_err(self) -> bool:
        """Return True if this is an Err result."""
        return True

    def unwrap(self) -> None:
        """Raise ValueError since this is an Err. For tests only."""
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_err(self) -> E:
        """Extract the error value. For tests/ergonomics only."""
        return self.error

    def map(self, fn: Callable[[T], U]) -> Err[E]:
        """Error propagates unchanged (short-circuit)."""
        return self

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Err[E]:
        """Error propagates unchanged (short-circuit)."""
        return self


# Type alias for Result union (Python 3.12+ compatible)
# With __future__ annotations, this is only evaluated during type checking
Result: TypeAlias = Ok[T] | Err[E]
