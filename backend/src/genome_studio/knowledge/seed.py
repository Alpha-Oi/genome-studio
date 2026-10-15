"""Seed-данные для BioKG.

Минимальный набор генов и путей для E. coli и yeast.
Достаточно для демонстрации MVP.
"""

from __future__ import annotations

from genome_studio.knowledge.graph import (
    BioKG,
    Edge,
    GeneNode,
    PathwayNode,
    RelationType,
)

ORGANISM_ECOLI = "Escherichia coli"
ORGANISM_YEAST = "Saccharomyces cerevisiae"


def build_default_kg() -> BioKG:
    """Собирает стартовый BioKG."""
    kg = BioKG()

    # --- E. coli genes ------------------------------------------------
    ecoli_genes = [
        GeneNode("ecoli.lacZ", "lacZ", ORGANISM_ECOLI, essential=False,
                 description="Beta-galactosidase, lactose metabolism"),
        GeneNode("ecoli.lacI", "lacI", ORGANISM_ECOLI, essential=False,
                 description="Lac repressor"),
        GeneNode("ecoli.recA", "recA", ORGANISM_ECOLI, essential=True,
                 description="DNA repair, essential"),
        GeneNode("ecoli.ftsZ", "ftsZ", ORGANISM_ECOLI, essential=True,
                 description="Cell division, essential"),
        GeneNode("ecoli.gfp", "GFP", ORGANISM_ECOLI, essential=False,
                 description="Green fluorescent protein (heterologous)"),
    ]
    for g in ecoli_genes:
        kg.add_gene(g)

    # --- E. coli pathways ---------------------------------------------
    kg.add_pathway(PathwayNode(
        "ecoli.lactose_metabolism", "Lactose metabolism", ORGANISM_ECOLI,
        produces=("galactose", "glucose"),
    ))
    kg.add_pathway(PathwayNode(
        "ecoli.cell_division", "Cell division", ORGANISM_ECOLI,
    ))

    # --- E. coli edges ------------------------------------------------
    kg.add_edge(Edge("ecoli.lacI", "ecoli.lacZ", RelationType.INHIBITS, 0.95))
    kg.add_edge(Edge("ecoli.lacZ", "ecoli.lactose_metabolism", RelationType.PART_OF, 0.9))
    kg.add_edge(Edge("ecoli.ftsZ", "ecoli.cell_division", RelationType.PART_OF, 0.95))
    kg.add_edge(Edge("ecoli.recA", "ecoli.ftsZ", RelationType.REGULATES, 0.6))

    # --- Yeast genes --------------------------------------------------
    yeast_genes = [
        GeneNode("yeast.GAL1", "GAL1", ORGANISM_YEAST, essential=False,
                 description="Galactokinase"),
        GeneNode("yeast.GAL4", "GAL4", ORGANISM_YEAST, essential=False,
                 description="Galactose regulator"),
        GeneNode("yeast.TPI1", "TPI1", ORGANISM_YEAST, essential=True,
                 description="Triose phosphate isomerase, essential"),
        GeneNode("yeast.ADH1", "ADH1", ORGANISM_YEAST, essential=False,
                 description="Alcohol dehydrogenase"),
    ]
    for g in yeast_genes:
        kg.add_gene(g)

    kg.add_pathway(PathwayNode(
        "yeast.galactose_metabolism", "Galactose metabolism", ORGANISM_YEAST,
        produces=("glucose-6-phosphate",),
    ))
    kg.add_pathway(PathwayNode(
        "yeast.ethanol_production", "Ethanol production", ORGANISM_YEAST,
        produces=("ethanol", "CO2"),
    ))

    kg.add_edge(Edge("yeast.GAL4", "yeast.GAL1", RelationType.ACTIVATES, 0.9))
    kg.add_edge(Edge("yeast.GAL1", "yeast.galactose_metabolism", RelationType.PART_OF, 0.9))
    kg.add_edge(Edge("yeast.ADH1", "yeast.ethanol_production", RelationType.PART_OF, 0.9))

    # --- CHO (для примера) --------------------------------------------
    cho_genes = [
        GeneNode("cho.GFP", "GFP", "Cricetulus griseus", essential=False,
                 description="Green fluorescent protein (heterologous)"),
        GeneNode("cho.BAX", "BAX", "Cricetulus griseus", essential=False,
                 description="Apoptosis regulator"),
        GeneNode("cho.BCL2", "BCL2", "Cricetulus griseus", essential=False,
                 description="Anti-apoptotic"),
    ]
    for g in cho_genes:
        kg.add_gene(g)

    kg.add_edge(Edge("cho.BCL2", "cho.BAX", RelationType.INHIBITS, 0.85))

    return kg