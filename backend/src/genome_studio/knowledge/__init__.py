"""BioKG - граф биологических знаний."""

from genome_studio.knowledge.graph import BioKG, GeneNode, PathwayNode, Edge
from genome_studio.knowledge.seed import build_default_kg

__all__ = ["BioKG", "GeneNode", "PathwayNode", "Edge", "build_default_kg"]