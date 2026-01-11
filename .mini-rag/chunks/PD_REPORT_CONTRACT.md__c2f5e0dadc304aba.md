### With Evidence Stop
```bash
$ uv run trifecta ctx get -s . --ids prime:abc123,skill:xyz456 \
  --mode excerpt --stop-on-evidence --query Foo --pd-report --max-chunks 3

Retrieved 1 chunk(s) (mode=excerpt, tokens=~245):
...
PD_REPORT v=1 stop_reason=evidence chunks_returned=1 chunks_requested=2 chars_returned_total=512 strong_hit=1 support=1
```
