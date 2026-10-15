"""CRISPR module - design of guide RNAs, PAM search, scoring."""

from genome_studio.crispr.designer import Guide, design_guides
from genome_studio.crispr.pam import find_pam_sites
from genome_studio.crispr.scoring import score_guide

__all__ = ["Guide", "design_guides", "find_pam_sites", "score_guide"]