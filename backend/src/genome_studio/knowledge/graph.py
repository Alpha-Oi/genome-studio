"""BioKG - минимальный граф знаний.

На старте - 10-20 узлов для E. coli и yeast.
Позже подключаем Reactome, KEGG, GO, STRING и т.д.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    GENE = "gene"
    PROTEIN = "protein"
    PATHWAY = "pathway"
    PHENOTYPE = "phenotype"


class RelationType(str, Enum):
    ENCODES = "encodes"
    PART_OF = "part_of"
    REGULATES = "regulates"
    ACTIVATES = "activates"
    INHIBITS = "inhibits"
    PRODUCES = "produces"
    AFFECTS = "affects"


@dataclass(frozen=True)
class GeneNode:
    """Ген."""

    id: str
    name: str
    organism: str
    essential: bool = False
    description: str = ""


@dataclass(frozen=True)
class PathwayNode:
    """Метаболический путь."""

    id: str
    name: str
    organism: str
    produces: tuple[str, ...] = ()


@dataclass(frozen=True)
class Edge:
    """Ребро графа."""

    source: str
    target: str
    relation: RelationType
    confidence: float = 0.8
    source_db: str = "seed"


@dataclass
class BioKG:
    """Граф знаний."""

    genes: dict[str, GeneNode] = field(default_factory=dict)
    pathways: dict[str, PathwayNode] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_gene(self, gene: GeneNode) -> None:
        self.genes[gene.id] = gene

    def add_pathway(self, pathway: PathwayNode) -> None:
        self.pathways[pathway.id] = pathway

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def get_gene(self, gene_id: str) -> GeneNode | None:
        return self.genes.get(gene_id)

    def find_gene_by_name(self, name: str, organism: str) -> GeneNode | None:
        """Ищет ген по имени и организму."""
        name_lower = name.lower()
        for gene in self.genes.values():
            if gene.name.lower() == name_lower and gene.organism == organism:
                return gene
        return None

    def outgoing(self, node_id: str, relation: RelationType | None = None) -> list[Edge]:
        """Исходящие рёбра."""
        result = [e for e in self.edges if e.source == node_id]
        if relation is not None:
            result = [e for e in result if e.relation == relation]
        return result

    def incoming(self, node_id: str, relation: RelationType | None = None) -> list[Edge]:
        """Входящие рёбра."""
        result = [e for e in self.edges if e.target == node_id]
        if relation is not None:
            result = [e for e in result if e.relation == relation]
        return result

    def pathways_of_gene(self, gene_id: str) -> list[PathwayNode]:
        """Пути, в которых участвует ген."""
        edges = self.outgoing(gene_id, RelationType.PART_OF)
        return [self.pathways[e.target] for e in edges if e.target in self.pathways]

    def genes_in_pathway(self, pathway_id: str) -> list[GeneNode]:
        """Гены в пути."""
        edges = self.incoming(pathway_id, RelationType.PART_OF)
        return [self.genes[e.source] for e in edges if e.source in self.genes]
