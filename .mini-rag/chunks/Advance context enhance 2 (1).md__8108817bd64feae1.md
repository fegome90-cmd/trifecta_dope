## The Problem with Loading Everything Upfront

When building coding agents, the typical approach is to load all relevant documentation into the prompt: API specs, design docs, runbooks, ADRs, configuration files. This works initially, but scales poorly.

The cost isn’t just tokens. It’s also accuracy. When you front-load dozens of documents, the agent:

- Cites the wrong section
- Mixes information from different versions
- Fixates on the first block it saw, ignoring better matches later
- Wastes inference on irrelevant content

This is exactly the pattern Anthropic describes for large tool libraries: too many definitions upfront degrade both cost and precision.
