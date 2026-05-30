"""
neo4j_layer/queries.py
======================
Shared Cypher query helpers used by all analysis modules.
Each function returns plain Python dicts/lists — identical shape to
what load_graph() returns from unified_graph.json, so modules need
minimal changes.

Usage:
    from neo4j_layer.queries import get_graph_data, is_neo4j_available
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

NEO4J_URI      = os.getenv("NEO4J_URI", "")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        try:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception:
            _driver = None
    return _driver


def is_neo4j_available() -> bool:
    """Ping Neo4j — returns True if reachable, False otherwise."""
    driver = _get_driver()
    if not driver:
        return False
    try:
        with driver.session() as s:
            s.run("RETURN 1")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Core data fetch — mirrors unified_graph.json structure
# ---------------------------------------------------------------------------
def _fetch_nodes(tx):
    result = tx.run("""
        MATCH (n)
        RETURN
            n.master_id       AS master_id,
            n.master_type     AS master_type,
            n.entity_types    AS entity_types,
            n.resolved_values AS resolved_values,
            n.source_entities AS source_entities
    """)
    return [dict(r) for r in result]


def _fetch_relations(tx):
    result = tx.run("""
        MATCH (src)-[r]->(tgt)
        RETURN
            src.master_id        AS source,
            tgt.master_id        AS target,
            type(r)              AS relation,
            r.source_type        AS source_type,
            r.timestamp          AS timestamp,
            r.confidence         AS confidence,
            r.attributes_json    AS attributes_json
    """)
    rows = []
    for rec in result:
        attrs = {}
        try:
            attrs = json.loads(rec["attributes_json"] or "{}")
        except Exception:
            pass
        rows.append({
            "source":      rec["source"],
            "target":      rec["target"],
            "relation":    rec["relation"],
            "source_type": rec["source_type"] or "",
            "timestamp":   rec["timestamp"] or "",
            "confidence":  float(rec["confidence"] or 1.0),
            "attributes":  attrs,
        })
    return rows


def get_graph_data() -> dict:
    """
    Returns {"master_entities": [...], "relations": [...]}
    identical to unified_graph.json shape.
    Raises RuntimeError if Neo4j unavailable.
    """
    driver = _get_driver()
    if not driver:
        raise RuntimeError("Neo4j driver unavailable")
    with driver.session() as session:
        nodes     = session.execute_read(_fetch_nodes)
        relations = session.execute_read(_fetch_relations)
    return {"master_entities": nodes, "relations": relations}


# ---------------------------------------------------------------------------
# Convenience wrappers for targeted queries
# ---------------------------------------------------------------------------
def get_financial_transfers() -> list:
    """Returns only TRANSFERRED_TO edges with parsed attributes."""
    driver = _get_driver()
    if not driver:
        raise RuntimeError("Neo4j driver unavailable")
    with driver.session() as session:
        result = session.run("""
            MATCH (src)-[r:TRANSFERRED_TO]->(tgt)
            RETURN
                src.master_id  AS source,
                tgt.master_id  AS target,
                r.timestamp    AS timestamp,
                r.attributes_json AS attributes_json
        """)
        rows = []
        for rec in result:
            attrs = {}
            try:
                attrs = json.loads(rec["attributes_json"] or "{}")
            except Exception:
                pass
            rows.append({
                "source":    rec["source"],
                "target":    rec["target"],
                "relation":  "TRANSFERRED_TO",
                "timestamp": rec["timestamp"] or "",
                "attributes": attrs,
            })
    return rows


def get_entity_source_types(master_id: str) -> list[str]:
    """Returns unique source_types of all edges connected to an entity."""
    driver = _get_driver()
    if not driver:
        raise RuntimeError("Neo4j driver unavailable")
    with driver.session() as session:
        result = session.run("""
            MATCH ({master_id: $mid})-[r]-()
            RETURN DISTINCT r.source_type AS source_type
        """, mid=master_id)
        return [r["source_type"] for r in result if r["source_type"]]
