import re
from pathlib import Path

def fix_file(p: Path):
    content = p.read_text()
    content = content.replace("from scripts.skill_hub_cards_core import (\n    RenderPlan,\n    SkillCard,\n    ClassifiedResult", "from src.application.skill_card_view_model import SkillCardViewModel\nfrom scripts.skill_hub_cards_core import (\n    RenderPlan,\n    ClassifiedResult")
    content = content.replace("from scripts.skill_hub_cards_core import (\n    RenderPlan,\n    SkillCard,\n    NormalizedResult", "from src.application.skill_card_view_model import SkillCardViewModel\nfrom scripts.skill_hub_cards_core import (\n    RenderPlan,\n    NormalizedResult")
    content = content.replace("old_card = SkillCard(id=", "old_card = SkillCardViewModel(id=")
    content = content.replace(", title=", ", name=")
    content = content.replace(", score=", ", relevance=")
    content = re.sub(r'cards=\[old_card\]', 'cards=[old_card]', content)
    content = content.replace('SkillCard(', 'SkillCardViewModel(')
    p.write_text(content)

fix_file(Path('tests/unit/test_skill_hub_renderer_handover.py'))
fix_file(Path('tests/unit/test_skill_hub_render_parity.py'))
