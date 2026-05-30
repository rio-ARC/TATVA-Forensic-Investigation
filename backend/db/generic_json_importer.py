import json
import os
import sys
import uuid
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.neo4j_client import Neo4jClient

def clean_label(name):
    """Sanitize label names for Neo4j."""
    if not name:
        return "Node"
    # Capitalize and remove non-alphanumeric
    cleaned = "".join(c for c in str(name) if c.isalnum() or c == "_")
    return cleaned if cleaned else "Node"

def clean_rel_type(name):
    """Sanitize relationship types for Neo4j."""
    if not name:
        return "HAS_VALUE"
    return "".join(c for c in str(name).upper() if c.isalnum() or c == "_")

def import_value(client, value, key_context="value", parent_id=None, parent_label=None):
    """
    Recursively imports arbitrary JSON values into Neo4j.
    Returns the ID of the created node (if a node was created).
    """
    if isinstance(value, dict):
        # Create a node for this object
        node_id = value.get("id") or value.get("master_id") or str(uuid.uuid4())
        
        # Determine labels: use 'type', 'master_type', 'label', or the key context
        type_hint = value.get("type") or value.get("master_type") or value.get("label") or key_context
        label = clean_label(type_hint)
        
        # Extract properties
        properties = {"id": node_id}
        child_elements = []
        
        for k, v in value.items():
            if k in ["id", "master_id", "type", "master_type", "label"]:
                continue
            
            if isinstance(v, (dict, list)):
                child_elements.append((k, v))
            else:
                # Flat properties
                safe_key = "".join(c for c in str(k) if c.isalnum() or c == "_")
                if safe_key:
                    properties[safe_key] = v
        
        # Merge node in Neo4j
        query = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props
        RETURN n.id as id
        """
        client.execute_write(query, {"id": node_id, "props": properties})
        
        # If there is a parent, create a relationship from parent to this node
        if parent_id and parent_label:
            rel_type = clean_rel_type(key_context)
            rel_query = f"""
            MATCH (p:{parent_label} {{id: $parent_id}})
            MATCH (c:{label} {{id: $child_id}})
            MERGE (p)-[:{rel_type}]->(c)
            """
            client.execute_write(rel_query, {
                "parent_id": parent_id,
                "child_id": node_id
            })
            
        # Process children
        for k, v in child_elements:
            import_value(client, v, key_context=k, parent_id=node_id, parent_label=label)
            
        return node_id
        
    elif isinstance(value, list):
        # If it's a list of dicts/lists, process each element
        # If it's a list of primitives, the parent caller would have stored it as a property
        node_ids = []
        for i, item in enumerate(value):
            # Use singular form or indexed key context
            item_id = import_value(client, item, key_context=f"{key_context}_item", parent_id=parent_id, parent_label=parent_label)
            if item_id:
                node_ids.append(item_id)
        return node_ids
        
    else:
        # Primitive value, normally handled by dict property assignment.
        # But if it's a top-level primitive, wrap it in a node.
        node_id = str(uuid.uuid4())
        label = clean_label(key_context)
        query = f"""
        MERGE (n:{label} {{id: $id}})
        SET n.value = $value
        """
        client.execute_write(query, {"id": node_id, "value": value})
        
        if parent_id and parent_label:
            rel_type = clean_rel_type(key_context)
            rel_query = f"""
            MATCH (p:{parent_label} {{id: $parent_id}})
            MATCH (c:{label} {{id: $child_id}})
            MERGE (p)-[:{rel_type}]->(c)
            """
            client.execute_write(rel_query, {
                "parent_id": parent_id,
                "child_id": node_id
            })
        return node_id

def detect_and_import(client, file_path):
    """
    Attempts to read JSON file.
    If it looks like a standard graph export (having 'nodes'/'entities' and 'relationships'/'relations' keys),
    it maps them directly.
    Otherwise, it recursively imports the JSON as a hierarchical document.
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Error: {file_path} does not exist.")
        return False
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Check if this matches a graph schema
    has_entities = any(k in data for k in ["entities", "nodes", "master_entities"])
    has_relations = any(k in data for k in ["relations", "relationships", "edges", "links"])
    
    if has_entities and has_relations:
        print(f"[Neo4j] Detected graph schema in {path.name}. Importing as unified graph...")
        # Resolve entity key
        entity_key = next(k for k in ["master_entities", "entities", "nodes"] if k in data)
        relation_key = next(k for k in ["relations", "relationships", "edges", "links"] if k in data)
        
        # We can map it using a structured importer logic
        from db.neo4j_importer import ingest_unified_graph
        # Adapt keys to fit the importer format
        adapted_data = {
            "master_entities": data[entity_key],
            "relations": data[relation_key]
        }
        dataset_label = clean_label(path.stem)
        ingest_unified_graph(client, adapted_data, dataset_label=dataset_label)
    else:
        print(f"[Neo4j] Importing {path.name} hierarchically as generic JSON...")
        # Import as arbitrary nested structure
        import_value(client, data, key_context=path.stem)
        
    print(f"[Neo4j] Generic import of {path.name} complete.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generic_json_importer.py <path_to_json_file>")
        sys.exit(1)
        
    json_file = sys.argv[1]
    client = Neo4jClient()
    if client.driver:
        # Note: We do NOT clear the DB automatically here since it could be used to load additional documents!
        detect_and_import(client, json_file)
        client.close()
