import re
from pathlib import Path

def fix(p_str):
    p = Path(p_str)
    c = p.read_text()
    c = re.sub(r'relevance=([\d.]+)', r'authority_state="healthy", relevance=\1', c)
    p.write_text(c)

fix('tests/unit/test_skill_hub_renderer_handover.py')
fix('tests/unit/test_skill_hub_render_parity.py')
