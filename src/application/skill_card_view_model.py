from __future__ import annotations

try:
    from scripts.skill_hub_runtime_ux import RuntimeSkillCard as SkillCardViewModel
except ImportError:
    from skill_hub_runtime_ux import RuntimeSkillCard as SkillCardViewModel  # type: ignore[no-redef]

__all__ = ["SkillCardViewModel"]
