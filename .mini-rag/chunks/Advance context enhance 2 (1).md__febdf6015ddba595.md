## 2. Programmatic Context Calling: Budget and Backpressure

The second bottleneck is context pollution. Even if you search well, if every `ctx.get()` dumps complete blocks into the prompt, you’re back to square one.

Anthropic explains this for tool outputs: large intermediate results pollute context and force more inference. The solution is the same: use a runtime as middleware.
