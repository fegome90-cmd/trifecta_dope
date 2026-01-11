## D) Exit Criteria

- [ ] Schema uses `segment_id`, no `mtime`
- [ ] Chunk IDs: `{doc}:{sha256(text)[:10]}`
- [ ] Digest: ≤2 chunks, ≤2000 tokens
- [ ] Search: score-based ranking (title=2, summary=1)
- [ ] Error strings exact and deterministic
- [ ] 140+ tests pass
- [ ] Zero legacy debt
- [ ] E2E: build→search→get verified
