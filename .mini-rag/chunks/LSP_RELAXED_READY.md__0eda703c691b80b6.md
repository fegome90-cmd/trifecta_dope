## Rationale
1.  **Latency Reduction**: Waiting for diagnostics can introduce significant delays, especially with large codebases or slow language servers.
2.  **Robustness**: Not all LSP servers guarantee immediate diagnostics upon initialization. Blocking until diagnostics arrive makes the client brittle and dependent on specific server behaviors.
3.  **Use Case Alignment**: Trifecta's primary use cases (symbol search, definition lookup) often require valid file references but do not inherently require a full diagnostic pass to be operational.
