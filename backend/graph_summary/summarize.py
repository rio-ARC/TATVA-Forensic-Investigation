"""
Graph Summary & Centrality Layer
=================================
Reads unified_graph.json → builds NetworkX graph → computes centrality
metrics and entity profiles → writes summary.json

Run standalone:
    cd backend
    python -m graph_summary.summarize
"""

import json
import math
from pathlib import Path
from datetime import datetime
from collections import Counter

# Neo4j integration (optional — falls back to JSON if unavailable)
try:
    from neo4j_layer.queries import get_graph_data, is_neo4j_available
    _NEO4J_IMPORTED = True
except ImportError:
    _NEO4J_IMPORTED = False

try:
    import networkx as nx
except ImportError:
    print("ERROR: networkx is required. Install via: pip install networkx")
    raise

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GRAPH_PATH = Path(__file__).parent.parent / "Graph_Integration_Layer" / "output" / "unified_graph.json"
OUTPUT_PATH = Path(__file__).parent / "summary.json"

# Timestamp formats found in unified_graph.json
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S+05:30",
]


# ---------------------------------------------------------------------------
# Graph Loading
# ---------------------------------------------------------------------------
def load_graph() -> dict:
    """
    Load graph data.
    Priority: Neo4j AuraDB → unified_graph.json (fallback).
    """
    if _NEO4J_IMPORTED and is_neo4j_available():
        try:
            print("[graph_summary] Using Neo4j as data source.")
            return get_graph_data()
        except Exception as e:
            print(f"[graph_summary] Neo4j failed ({e}), falling back to JSON.")
    # JSON fallback
    print("[graph_summary] Using unified_graph.json (fallback).")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Name Resolution
# ---------------------------------------------------------------------------
def get_entity_name(master: dict) -> str:
    """
    Extract the best human-readable name for a master entity.
    Priority: person name > account > first resolved value > master_id
    Filters out junk values (newlines, empty, very long strings).
    """
    resolved = master.get("resolved_values", [])
    entity_types = master.get("entity_types", [])
    master_type = master.get("master_type", "")

    # For PERSON types, prefer the name-like resolved values
    if master_type == "PERSON" or "PERSON" in entity_types:
        for val in resolved:
            if not val:
                continue
            # Skip values that look like IDs, phone numbers, device IDs, account IDs
            if val.startswith("acc") or val.startswith("android_") or val.startswith("watch_"):
                continue
            if val.replace(" ", "").isdigit():
                continue
            if val.startswith("@"):
                continue
            # Skip junk values with newlines or very long strings
            if "\n" in val or len(val) > 50:
                continue
            return val.title()

    # For PLACE types, use the first resolved value
    if master_type == "PLACE":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.title()

    # For INFRASTRUCTURE types (towers, platforms, cameras)
    if master_type == "INFRASTRUCTURE":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.title()

    # For ENTITY types (accounts, vehicles, trackers)
    if master_type == "ENTITY":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.upper() if val.startswith("acc") else val.title()

    # Fallback: first valid resolved value
    for val in resolved:
        if val and "\n" not in val and len(val) < 80:
            return val.title()

    return master.get("master_id", "Unknown")


def build_name_map(masters: list) -> dict:
    """Build a mapping of master_id → human-readable name."""
    return {m["master_id"]: get_entity_name(m) for m in masters}


# ---------------------------------------------------------------------------
# Timestamp Parsing
# ---------------------------------------------------------------------------
def parse_timestamp(ts_str: str) -> datetime | None:
    """Try parsing a timestamp string with multiple known formats."""
    if not ts_str:
        return None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except (ValueError, TypeError):
            continue
    # Last resort: try fromisoformat (handles many ISO 8601 variants)
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# NetworkX Graph Construction
# ---------------------------------------------------------------------------
def build_networkx_graph(graph: dict) -> nx.DiGraph:
    """
    Build a NetworkX DiGraph from the unified graph.
    - Nodes = master entities (with master_type, entity_types as attrs)
    - Edges = relations (with relation type, confidence, source_type as attrs)
    """
    G = nx.DiGraph()

    # Add nodes
    for master in graph.get("master_entities", []):
        G.add_node(
            master["master_id"],
            master_type=master.get("master_type", "UNKNOWN"),
            entity_types=master.get("entity_types", []),
            resolved_values=master.get("resolved_values", []),
        )

    # Add edges — use a key to allow multigraph-like parallel edges
    # Since DiGraph doesn't support parallel edges, we aggregate
    for rel in graph.get("relations", []):
        src = rel.get("source")
        tgt = rel.get("target")
        if src and tgt:
            # If edge already exists, we still add it (overwrites, but that's
            # okay since we just need graph topology for centrality)
            G.add_edge(
                src, tgt,
                relation=rel.get("relation", "UNKNOWN"),
                confidence=rel.get("confidence", 0.0),
                source_type=rel.get("source_type", rel.get("provenance", "unknown")),
            )

    return G


# ---------------------------------------------------------------------------
# Entity Type & Relation Counts
# ---------------------------------------------------------------------------
def compute_entity_counts(masters: list) -> dict:
    """Count entities by master_type."""
    counter = Counter(m.get("master_type", "UNKNOWN") for m in masters)
    return dict(sorted(counter.items(), key=lambda x: -x[1]))


def compute_relation_counts(relations: list) -> dict:
    """Count relations by type."""
    counter = Counter(r.get("relation", "UNKNOWN") for r in relations)
    return dict(sorted(counter.items(), key=lambda x: -x[1]))


# ---------------------------------------------------------------------------
# Source Types
# ---------------------------------------------------------------------------
def collect_data_sources(relations: list) -> list:
    """Collect all unique data source types across relations."""
    sources = set()
    for rel in relations:
        st = rel.get("source_type")
        prov = rel.get("provenance", "")
        if st:
            sources.add(st)
        elif prov:
            # Extract source from provenance like "emails.txt:header" → "email"
            base = prov.split(":")[0].replace(".txt", "").replace(".json", "")
            sources.add(base)
    return sorted(sources)


# ---------------------------------------------------------------------------
# Centrality Computation
# ---------------------------------------------------------------------------
def compute_centrality(G: nx.DiGraph) -> dict:
    """
    Compute multiple centrality metrics for each node.
    Returns: { master_id: { degree, betweenness, in_degree, out_degree, pagerank } }
    """
    if G.number_of_nodes() == 0:
        return {}

    degree_c = nx.degree_centrality(G)
    betweenness_c = nx.betweenness_centrality(G)
    in_degree_c = nx.in_degree_centrality(G)
    out_degree_c = nx.out_degree_centrality(G)

    try:
        pagerank_c = nx.pagerank(G, max_iter=200)
    except nx.PowerIterationFailedConvergence:
        pagerank_c = {n: 0.0 for n in G.nodes()}

    result = {}
    for node in G.nodes():
        result[node] = {
            "degree_centrality": round(degree_c.get(node, 0.0), 4),
            "betweenness_centrality": round(betweenness_c.get(node, 0.0), 4),
            "in_degree_centrality": round(in_degree_c.get(node, 0.0), 4),
            "out_degree_centrality": round(out_degree_c.get(node, 0.0), 4),
            "pagerank": round(pagerank_c.get(node, 0.0), 4),
        }

    return result


# ---------------------------------------------------------------------------
# Incident Window
# ---------------------------------------------------------------------------
def compute_incident_window(relations: list) -> dict:
    """
    Find the earliest and latest timestamps to determine the incident window.
    """
    timestamps = []
    for rel in relations:
        ts = parse_timestamp(rel.get("timestamp", ""))
        if ts:
            # Normalize to naive datetime for comparison
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
            timestamps.append(ts)

    if not timestamps:
        return {"start": None, "end": None, "duration_minutes": 0}

    earliest = min(timestamps)
    latest = max(timestamps)
    duration = (latest - earliest).total_seconds() / 60

    return {
        "start": earliest.isoformat(),
        "end": latest.isoformat(),
        "duration_minutes": round(duration, 1),
    }


# ---------------------------------------------------------------------------
# Entity Profiles
# ---------------------------------------------------------------------------
def build_entity_profiles(
    masters: list,
    relations: list,
    centrality: dict,
    name_map: dict,
) -> list:
    """
    Build a rich profile for each master entity, combining:
    - Basic info (name, type, resolved values)
    - Centrality scores
    - Source type coverage
    - Relation counts
    """
    # Pre-compute per-entity relation data
    entity_source_types = {}   # master_id → set of source_types
    entity_relation_count = Counter()  # master_id → count of relations
    entity_relation_types = {}  # master_id → set of relation types

    for rel in relations:
        src = rel.get("source")
        tgt = rel.get("target")
        st = rel.get("source_type", rel.get("provenance", "unknown"))

        for eid in [src, tgt]:
            if eid:
                entity_relation_count[eid] += 1
                if eid not in entity_source_types:
                    entity_source_types[eid] = set()
                entity_source_types[eid].add(st)
                if eid not in entity_relation_types:
                    entity_relation_types[eid] = set()
                entity_relation_types[eid].add(rel.get("relation", "UNKNOWN"))

    profiles = []
    for master in masters:
        mid = master["master_id"]
        c = centrality.get(mid, {})

        # Filter resolved values (remove junk)
        clean_resolved = [
            v for v in master.get("resolved_values", [])
            if v and "\n" not in v and len(v) < 80
        ]

        source_types = sorted(entity_source_types.get(mid, set()))

        profile = {
            "master_id": mid,
            "name": name_map.get(mid, mid),
            "master_type": master.get("master_type", "UNKNOWN"),
            "entity_types": master.get("entity_types", []),
            "resolved_values": clean_resolved,
            "degree_centrality": c.get("degree_centrality", 0.0),
            "betweenness_centrality": c.get("betweenness_centrality", 0.0),
            "in_degree_centrality": c.get("in_degree_centrality", 0.0),
            "out_degree_centrality": c.get("out_degree_centrality", 0.0),
            "pagerank": c.get("pagerank", 0.0),
            "source_types": source_types,
            "source_count": len(source_types),
            "relation_count": entity_relation_count.get(mid, 0),
            "relation_types": sorted(entity_relation_types.get(mid, set())),
        }
        profiles.append(profile)

    # Sort by degree centrality (most connected first)
    profiles.sort(key=lambda p: p["degree_centrality"], reverse=True)
    return profiles


# ---------------------------------------------------------------------------
# Key Actors Detection
# ---------------------------------------------------------------------------
def identify_key_actors(profiles: list, top_n: int = 10) -> list:
    """
    Identify the top-N most important entities based on a composite score.
    Composite = 0.35*degree + 0.25*betweenness + 0.20*pagerank + 0.10*source_diversity + 0.10*relation_volume
    """
    if not profiles:
        return []

    # Normalize relation_count and source_count across all profiles
    max_rel = max(p["relation_count"] for p in profiles) or 1
    max_src = max(p["source_count"] for p in profiles) or 1

    scored = []
    for p in profiles:
        composite = (
            0.35 * p["degree_centrality"]
            + 0.25 * p["betweenness_centrality"]
            + 0.20 * p["pagerank"]
            + 0.10 * (p["source_count"] / max_src)
            + 0.10 * (p["relation_count"] / max_rel)
        )
        scored.append({
            "master_id": p["master_id"],
            "name": p["name"],
            "master_type": p["master_type"],
            "composite_score": round(composite, 4),
            "degree_centrality": p["degree_centrality"],
            "betweenness_centrality": p["betweenness_centrality"],
            "pagerank": p["pagerank"],
            "source_count": p["source_count"],
            "relation_count": p["relation_count"],
        })

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Network Topology Stats
# ---------------------------------------------------------------------------
def compute_topology_stats(G: nx.DiGraph) -> dict:
    """Compute graph-level topology statistics."""
    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "is_weakly_connected": nx.is_weakly_connected(G),
    }

    # Connected components
    weak_components = list(nx.weakly_connected_components(G))
    stats["weakly_connected_components"] = len(weak_components)
    stats["largest_component_size"] = max(len(c) for c in weak_components) if weak_components else 0

    # Average clustering (on undirected version)
    G_undirected = G.to_undirected()
    stats["average_clustering"] = round(nx.average_clustering(G_undirected), 4)

    # Degree distribution stats
    degrees = [d for _, d in G.degree()]
    if degrees:
        stats["avg_degree"] = round(sum(degrees) / len(degrees), 2)
        stats["max_degree"] = max(degrees)
        stats["min_degree"] = min(degrees)

    return stats


# ---------------------------------------------------------------------------
# Financial Flow Summary
# ---------------------------------------------------------------------------
def compute_financial_summary(relations: list, name_map: dict) -> dict:
    """
    Summarize all TRANSFERRED_TO relations:
    total volume, number of transfers, unique accounts involved, flow chains.
    """
    transfers = [r for r in relations if r.get("relation") == "TRANSFERRED_TO"]

    if not transfers:
        return {"total_volume": 0, "transfer_count": 0, "unique_accounts": []}

    total_volume = sum(r.get("attributes", {}).get("amount", 0) for r in transfers)
    unique_accounts = set()
    for r in transfers:
        unique_accounts.add(r["source"])
        unique_accounts.add(r["target"])

    # Group by source → target flow
    flows = {}
    for r in transfers:
        key = f"{name_map.get(r['source'], r['source'])} → {name_map.get(r['target'], r['target'])}"
        if key not in flows:
            flows[key] = {"total_amount": 0, "count": 0, "methods": set()}
        flows[key]["total_amount"] += r.get("attributes", {}).get("amount", 0)
        flows[key]["count"] += 1
        method = r.get("attributes", {}).get("transaction_type", "unknown")
        flows[key]["methods"].add(method)

    # Convert sets to lists for JSON
    flow_list = []
    for path, data in sorted(flows.items(), key=lambda x: -x[1]["total_amount"]):
        flow_list.append({
            "flow": path,
            "total_amount": data["total_amount"],
            "transfer_count": data["count"],
            "methods": sorted(data["methods"]),
        })

    return {
        "total_volume": total_volume,
        "transfer_count": len(transfers),
        "unique_accounts_involved": len(unique_accounts),
        "top_flows": flow_list,
    }


# ---------------------------------------------------------------------------
# Communication Summary
# ---------------------------------------------------------------------------
def compute_communication_summary(relations: list, name_map: dict) -> dict:
    """
    Summarize communication patterns: calls, messages, emails.
    """
    comm_types = {"CALLED", "MESSAGED", "EMAILED"}
    comms = [r for r in relations if r.get("relation") in comm_types]

    if not comms:
        return {"total_communications": 0}

    by_type = Counter(r["relation"] for r in comms)

    # Call duration stats
    call_durations = [
        r.get("attributes", {}).get("duration", 0)
        for r in comms if r.get("relation") == "CALLED"
    ]

    # Most active communicators
    comm_counter = Counter()
    for r in comms:
        src_name = name_map.get(r["source"], r["source"])
        comm_counter[src_name] += 1

    return {
        "total_communications": len(comms),
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "total_call_duration_seconds": sum(call_durations),
        "avg_call_duration_seconds": round(sum(call_durations) / len(call_durations), 1) if call_durations else 0,
        "most_active_communicators": [
            {"name": name, "count": count}
            for name, count in comm_counter.most_common(5)
        ],
    }


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def run_summary() -> dict:
    """
    Run the full graph summary pipeline and save results to summary.json.
    """
    print(f"Loading graph from: {GRAPH_PATH}")
    graph = load_graph()

    masters = graph.get("master_entities", [])
    relations = graph.get("relations", [])

    print(f"  Entities: {len(masters)}, Relations: {len(relations)}")

    # Build name map
    name_map = build_name_map(masters)

    # Build NetworkX graph
    print("  Building NetworkX graph...")
    G = build_networkx_graph(graph)

    # Compute everything
    print("  Computing centrality metrics...")
    centrality = compute_centrality(G)

    print("  Building entity profiles...")
    profiles = build_entity_profiles(masters, relations, centrality, name_map)

    print("  Identifying key actors...")
    key_actors = identify_key_actors(profiles)

    print("  Computing topology stats...")
    topology = compute_topology_stats(G)

    print("  Computing financial summary...")
    financial = compute_financial_summary(relations, name_map)

    print("  Computing communication summary...")
    communication = compute_communication_summary(relations, name_map)

    print("  Computing incident window...")
    incident_window = compute_incident_window(relations)

    # Assemble final output
    summary = {
        "generated_at": datetime.now().isoformat(),
        "overview": {
            "total_entities": len(masters),
            "total_relations": len(relations),
            "entity_type_counts": compute_entity_counts(masters),
            "relation_type_counts": compute_relation_counts(relations),
            "incident_window": incident_window,
            "data_sources_present": collect_data_sources(relations),
        },
        "topology": topology,
        "key_actors": key_actors,
        "financial_summary": financial,
        "communication_summary": communication,
        "entity_profiles": profiles,
    }

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[OK] Summary saved to: {OUTPUT_PATH}")
    print(f"     Total entities profiled: {len(profiles)}")
    print(f"     Key actors identified: {len(key_actors)}")
    print(f"     Financial volume: Rs.{financial.get('total_volume', 0):,}")

    return summary


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_summary()
