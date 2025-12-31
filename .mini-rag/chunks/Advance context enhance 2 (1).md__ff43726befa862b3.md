## 1. Context Search: Progressive Disclosure

Instead of loading everything, define a lightweight Context Search interface and keep chunks deferred. The agent starts with:

- A short digest (L0)
- An index of available documents (L0)
- A search capability: `ctx.search`

Then it discovers relevant chunks on demand, just like Tool Search Tool discovers tools.
