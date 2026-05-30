"""
neo4j_layer/loader.py
=====================
Loads unified_graph.json into Neo4j AuraDB.

Run:
    cd backend
    python -m neo4j_layer.loader

Requirements:
    pip install neo4j python-dotenv
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
except ImportError:
    print("ERROR: Install neo4j driver → pip install neo4j")
    raise

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).parent.parent / ".env")

NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j+s://your-auradb-id.databases.neo4j.io")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

GRAPH_PATH = (
    Path(__file__).parent.parent
    / "Graph_Integration_Layer" / "output" / "unified_graph.json"
)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _load_nodes(tx, entities: list):
    """MERGE each master entity as a Neo4j node, labelled by master_type."""
    for e in entities:
        label = e.get("master_type", "ENTITY")
        tx.run(
            f"""
            MERGE (n:{label} {{master_id: $master_id}})
            SET
                n.master_type     = $master_type,
                n.entity_types    = $entity_types,
                n.resolved_values = $resolved_values,
                n.source_entities = $source_entities
            """,
            master_id      = e["master_id"],
            master_type    = e.get("master_type", "ENTITY"),
            entity_types   = e.get("entity_types", []),
            resolved_values= e.get("resolved_values", []),
            source_entities= e.get("source_entities", []),
        )


def _load_relations(tx, relations: list):
    """MERGE each relation as a directed Neo4j edge."""
    for r in relations:
        rel_type = r.get("relation", "RELATED_TO").replace(" ", "_").upper()
        attrs    = r.get("attributes", {})
        tx.run(
            f"""
            MATCH (src {{master_id: $source}})
            MATCH (tgt {{master_id: $target}})
            MERGE (src)-[rel:{rel_type} {{
                source_type: $source_type,
                timestamp:   $timestamp
            }}]->(tgt)
            SET
                rel.confidence  = $confidence,
                rel.attributes  = $attributes_json
            """,
            source        = r["source"],
            target        = r["target"],
            source_type   = r.get("source_type", ""),
            timestamp     = r.get("timestamp", ""),
            confidence    = float(r.get("confidence", 1.0)),
            attributes_json = json.dumps(attrs),
        )


# ---------------------------------------------------------------------------
# Constraints (run once)
# ---------------------------------------------------------------------------
def _create_constraints(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:PERSON)           REQUIRE n.master_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:PLACE)            REQUIRE n.master_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:ENTITY)           REQUIRE n.master_id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:INFRASTRUCTURE)   REQUIRE n.master_id IS UNIQUE")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def load_graph_to_neo4j():
    if not GRAPH_PATH.exists():
        print(f"ERROR: unified_graph.json not found at {GRAPH_PATH}")
        return

    print(f"[LOADER] Reading {GRAPH_PATH}")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        graph = json.load(f)

    entities  = graph.get("master_entities", [])
    relations = graph.get("relations", [])
    print(f"[LOADER] {len(entities)} entities | {len(relations)} relations")

    driver = get_driver()
    try:
        with driver.session() as session:
            print("[LOADER] Creating constraints...")
            session.execute_write(_create_constraints)

            print("[LOADER] Loading nodes (MERGE)...")
            # Batch in chunks of 200 for efficiency
            chunk = 200
            for i in range(0, len(entities), chunk):
                session.execute_write(_load_nodes, entities[i:i+chunk])
                print(f"         nodes {i+chunk}/{len(entities)}", end="\r")
            print()

            print("[LOADER] Loading relations (MERGE)...")
            for i in range(0, len(relations), chunk):
                session.execute_write(_load_relations, relations[i:i+chunk])
                print(f"         rels  {i+chunk}/{len(relations)}", end="\r")
            print()

        print("[LOADER] ✓ Done. Graph loaded into Neo4j AuraDB.")
    finally:
        driver.close()


if __name__ == "__main__":
    load_graph_to_neo4j()
