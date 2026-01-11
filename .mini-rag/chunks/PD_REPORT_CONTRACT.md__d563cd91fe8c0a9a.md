### Basic
```bash
$ uv run trifect ctx get -s . --ids prime:abc123,skill:xyz456 --mode excerpt --pd-report

Retrieved 2 chunk(s) (mode=excerpt, tokens=~450):
...
PD_REPORT v=1 stop_reason=complete chunks_returned=2 chunks_requested=2 chars_returned_total=1024 strong_hit=0 support=0
```
