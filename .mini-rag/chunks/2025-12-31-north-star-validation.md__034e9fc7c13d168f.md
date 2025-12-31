ropagates unchanged

    def and_then(self, fn: Callable) -> Err[E]:
        return self  # Short-circuit


# Type alias for convenience
Result = Ok[T] | Err[E]
```
