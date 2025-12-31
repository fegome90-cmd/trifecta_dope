# Advanced Context Use: Context as Invokable Tools

Large language models can now handle massive context windows—200K tokens and beyond. But having the capacity to process information doesn’t mean we’re using it effectively. In production systems, the bottleneck isn’t whether the model can understand code or documentation. It’s more mundane: the agent can’t find the right part of the context, or it finds it but drowns in irrelevant text.

Even with huge context windows, dumping everything upfront causes real problems. Research shows that LLMs struggle to use information buried in the middle of long inputs—a phenomenon known as “lost in the middle” (Liu et al., 2023, “Lost in the Middle: How Language Models Use Long Contexts”). The model’s attention degrades as context grows, especially for information that isn’t at the beginning or end.

Anthropic’s recent post on [advanced tool use] outlines three improvements: discovering tools on demand, orchestrating them from code, and teaching correct usage with examples. This post applies the same pattern, but instead of tools, we treat context chunks as invokable resources.

The match is 1:1:

- **Tool Search Tool** → **Context Search**
- **Programmatic Tool Calling** → **Programmatic Context Calling**
- **Tool Use Examples** → **Context Use Examples**
