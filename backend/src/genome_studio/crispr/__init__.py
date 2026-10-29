"""CRISPR module - design of guide RNAs, PAM search, scoring, off-target."""

from genome_studio.crispr.designer import Guide, design_guides
from genome_studio.crispr.offtarget import (
    OffTargetHit,
    find_offtargets,
    off_target_risk,
)
from genome_studio.crispr.pam import find_pam_sites
from genome_studio.crispr.scoring import score_guide

__all__ = [
    "Guide",
    "OffTargetHit",
    "design_guides",
    "find_offtargets",
    "find_pam_sites",
    "off_target_risk",
    "score_guide",
]
