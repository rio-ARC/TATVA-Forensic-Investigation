import json
import os
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.neo4j_client import Neo4jClient

def clear_database(client):
    """Deletes all nodes and relationships from the database. Use with caution!"""
    print("[Neo4j] Clearing existing database...")
    query = "MATCH (n) DETACH DELETE n"
    client.execute_write(query)

def ingest_unified_graph(client, graph_data, dataset_label="UnifiedGraph"):
    """
    Ingests the unified_graph.json into Neo4j, partitioning it under a dataset label.
    
    Graph structure:
      master_entities[]: master_id, master_type, entity_types, resolved_values, source_entities
      relations[]:       source, target, relation, attributes, timestamp, confidence, source_type
    """
    master_entities = graph_data.get("master_entities", [])
    relations = graph_data.get("relations", [])
    
    # Sanitize dataset_label
    dataset_label = "".join(c for c in str(dataset_label) if c.isalnum() or c == "_")
    if not dataset_label:
        dataset_label = "UnifiedGraph"
    
    # ── ENTITIES ──────────────────────────────────────────────────
    print(f"[Neo4j] Ingesting {len(master_entities)} master entities for dataset '{dataset_label}'...")
    
    # Group entities by master_type for typed Neo4j labels
    entities_by_type = {}
    for entity in master_entities:
        e_type = entity.get("master_type") or entity.get("type") or entity.get("label") or "Entity"
        # Ensure valid Neo4j label (alphanumeric + underscore only)
        safe_type = "".join(c for c in str(e_type) if c.isalnum() or c == "_")
        if not safe_type:
            safe_type = "Entity"
            
        if safe_type not in entities_by_type:
            entities_by_type[safe_type] = []
            
        # Resolve the best ID (master_id first, then temp_id, then id)
        node_id = entity.get("master_id") or entity.get("temp_id") or entity.get("id")
        if not node_id:
            import uuid
            node_id = f"GEN_{uuid.uuid4().hex[:8]}"
            
        # Build flat property dict for Neo4j
        props = {"id": node_id}
        
        # Store entity_types as a JSON string
        if "entity_types" in entity:
            props["entity_types"] = json.dumps(entity["entity_types"])
            
        # Store resolved_values as a JSON string
        if "resolved_values" in entity:
            props["resolved_values"] = json.dumps(entity["resolved_values"])
        
        # Flatten attributes or resolved_values into individual properties if it's a dict
        resolved = entity.get("attributes") or {}
        if isinstance(resolved, dict):
            for rk, rv in resolved.items():
                safe_key = "".join(c for c in str(rk) if c.isalnum() or c == "_")
                if safe_key:
                    if isinstance(rv, (dict, list)):
                        props[safe_key] = json.dumps(rv)
                    elif rv is not None:
                        props[safe_key] = rv
        
        # Store source_entities as a JSON string (for traceability)
        if "source_entities" in entity:
            props["source_entities"] = json.dumps(entity["source_entities"])
        
        # Carry over master_type or type as a property too
        props["master_type"] = e_type
        props["dataset"] = dataset_label
            
        entities_by_type[safe_type].append(props)

    for e_type, batch in entities_by_type.items():
        print(f"  -> {e_type}:{dataset_label}: {len(batch)} nodes")
        query = f"""
        UNWIND $batch AS props
        MERGE (n:{e_type}:{dataset_label} {{id: props.id}})
        SET n += props
        """
        client.execute_write(query, {"batch": batch})
        
    # ── RELATIONS ─────────────────────────────────────────────────
    print(f"[Neo4j] Ingesting {len(relations)} relations for dataset '{dataset_label}'...")
    
    relations_by_type = {}
    skipped = 0
    for rel in relations:
        r_type = rel.get("relation", rel.get("type", "RELATED_TO"))
        safe_type = "".join(c for c in str(r_type) if c.isalnum() or c == "_").upper()
        if not safe_type:
            safe_type = "RELATED_TO"
            
        if safe_type not in relations_by_type:
            relations_by_type[safe_type] = []
            
        source = rel.get("source")
        target = rel.get("target")
        
        if not source or not target:
            skipped += 1
            continue
        
        # Build flat relation properties
        props = {}
        for k in ("timestamp", "confidence", "source_type"):
            v = rel.get(k)
            if v is not None:
                props[k] = str(v) if isinstance(v, (dict, list)) else v
        
        # attributes is a dict — flatten it
        attrs = rel.get("attributes", {})
        if isinstance(attrs, dict):
            for ak, av in attrs.items():
                safe_key = "attr_" + "".join(c for c in str(ak) if c.isalnum() or c == "_")
                if isinstance(av, (dict, list)):
                    props[safe_key] = json.dumps(av)
                elif av is not None:
                    props[safe_key] = av
                    
        relations_by_type[safe_type].append({
            "source": source,
            "target": target,
            "props": props
        })
    
    if skipped:
        print(f"  [WARN] Skipped {skipped} relations with missing source/target")
            
    for r_type, batch in relations_by_type.items():
        print(f"  -> {r_type}: {len(batch)} edges")
        query = f"""
        UNWIND $batch AS rel
        MATCH (s:{dataset_label} {{id: rel.source}})
        MATCH (t:{dataset_label} {{id: rel.target}})
        MERGE (s)-[r:{r_type}]->(t)
        SET r += rel.props
        SET r.dataset = $dataset_label
        """
        client.execute_write(query, {"batch": batch, "dataset_label": dataset_label})
        
    print(f"[Neo4j] Ingestion of dataset '{dataset_label}' complete.")

# ── MAIN ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    graph_path = Path(__file__).parent.parent / "Graph_Integration_Layer" / "output" / "unified_graph.json"
    
    if not graph_path.exists():
        print(f"Error: {graph_path} does not exist. Run the integration layer first.")
        sys.exit(1)
        
    with open(graph_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
        
    client = Neo4jClient()
    
    if client.driver:
        clear_database(client)
        ingest_unified_graph(client, graph_data)
        client.close()
    else:
        print("Aborting: could not connect to Neo4j.")
        sys.exit(1)
