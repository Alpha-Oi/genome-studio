"""BioKG - граф биологических знаний."""

from genome_studio.knowledge.graph import BioKG, Edge, GeneNode, PathwayNode
from genome_studio.knowledge.seed import build_default_kg

__all__ = ["BioKG", "Edge", "GeneNode", "PathwayNode", "build_default_kg"]
