### How it works

Instead of chunks falling directly into the model’s context:

1. The agent decides what it needs (`ctx.search`)
2. The runtime fetches multiple chunks (`ctx.get`)
3. The runtime reduces/normalizes/compacts
4. The model sees only relevant summaries/excerpts

This is Programmatic Tool Calling for context: Claude writes or uses code to orchestrate what enters the context.
