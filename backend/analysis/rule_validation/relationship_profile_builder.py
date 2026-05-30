"""
relationship_profile_builder.py
=================================
Builds relationship profiles and enriches them with human-readable explanations.
"""

from risk_scorer import compute_relationship_risk_profiles
from explanation_builder import build_relationship_explanation

def build_relationship_profiles(relations: list, masters: dict, name_map: dict) -> list[dict]:
    """
    Computes relationship profiles and adds natural-language explanations to each.
    """
    profiles = compute_relationship_risk_profiles(relations, masters, name_map)
    for p in profiles:
        p["explanation"] = build_relationship_explanation(p)
    return profiles
