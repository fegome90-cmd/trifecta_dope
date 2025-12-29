"""Domain Constants."""

MAX_SKILL_LINES = 100

VALID_PROFILES = [
    "diagnose_micro",
    "impl_patch",
    "only_code",
    "plan",
    "handoff_log",
]


def validate_profile(profile: str) -> str:
    """
    Validate and return profile name.

    Args:
        profile: Profile name to validate

    Returns:
        Validated profile name

    Raises:
        ValueError: If profile is not valid
    """
    if profile not in VALID_PROFILES:
        raise ValueError(
            f"Invalid profile '{profile}'. "
            f"Valid profiles: {', '.join(VALID_PROFILES)}"
        )
    return profile
