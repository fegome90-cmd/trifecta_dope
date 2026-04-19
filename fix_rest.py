from pathlib import Path
for p in [Path('tests/unit/test_skill_hub_renderer_handover.py'), Path('tests/unit/test_skill_hub_render_parity.py')]:
    c = p.read_text()
    c = c.replace("raw_name=", "raw_title=")
    c = c.replace("visible_name=", "visible_title=")
    # score instead of relevance for NormalizedResult
    c = c.replace("relevance=0.9", "score=0.9")
    c = c.replace("relevance=0.95", "score=0.95")
    p.write_text(c)
