from enum import Enum


class CoachingFocus(str, Enum):
    """Focus areas for coaching sessions."""

    TECHNIQUE = "technique"
    FITNESS = "fitness"
    TACTICS = "tactics"
    MENTAL = "mental"
    SPECIFIC_SKILLS = "specific_skills"
    GAME_SITUATION = "game_situation"
