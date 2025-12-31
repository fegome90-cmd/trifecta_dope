## Validation Checklist

- `pytest tests/unit/test_session_protocol_templates.py -v`
- `pytest tests/unit/test_session_writer.py -v`
- `pytest tests/unit/test_claude_wrapper.py -v`
- `pytest tests/unit/test_ci_session_gate.py -v`
- `make trifecta-validate PATH=<segment>`
