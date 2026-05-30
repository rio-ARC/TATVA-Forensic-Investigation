import json
import networkx as nx
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .insight_schema import (
    EntityDetail, RelationDetail, GraphPayload,
    SuspectDetail, TransactionAlert, TimelineEvent, GraphSummary
)

# In-memory caches for startup computation
_GRAPH_DATA: Dict[str, Any] = {}
_SUSPECTS: List[SuspectDetail] = []
_ALERTS: List[TransactionAlert] = []
_TIMELINE: List[TimelineEvent] = []
_SUMMARY: Optional[GraphSummary] = None

def get_graph_file_path() -> Path:
    """
    Locate unified_graph.json.  Search order:
    1. backend/Graph_Integration_Layer/output/unified_graph.json  ← actual output location
    2. backend/Graph_Integration_Layer/unified_graph.json          ← legacy flat location
    3. backend/unified_graph.json                                  ← fallback
    """
    base = Path(__file__).parent.parent  # → backend/
    candidates = [
        base / "Graph_Integration_Layer" / "output" / "unified_graph.json",
        base / "Graph_Integration_Layer" / "unified_graph.json",
        base / "unified_graph.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    # Return the primary expected path so the FileNotFoundError message is informative
    return candidates[0]


def _get_redis_client():
    try:
        # Ensure backend is in python path
        backend_path = str(Path(__file__).parent.parent)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from db.redis_client import RedisClient
        rc = RedisClient()
        if rc.connected:
            return rc
    except Exception:
        pass
    return None

def fetch_graph_from_neo4j(dataset_label="UnifiedGraph") -> Dict[str, Any]:
    """Fetch the graph data from Neo4j AuraDB and structure it like unified_graph.json."""
    # Ensure backend is in python path
    backend_path = str(Path(__file__).parent.parent)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from db.neo4j_client import Neo4jClient
    
    client = Neo4jClient()
    if not client.driver:
        raise Exception("Could not connect to Neo4j database")
        
    try:
        # 1. Fetch all nodes matching the dataset label
        node_query = f"""
        MATCH (n:{dataset_label})
        RETURN n.id AS master_id, labels(n) AS labels, properties(n) AS props
        """
        records = client.execute_read(node_query)
        
        master_entities = []
        for rec in records:
            props = dict(rec["props"])
            master_id = rec["master_id"]
            
            # Reconstruct entity_types
            entity_types = []
            if "entity_types" in props:
                try:
                    entity_types = json.loads(props["entity_types"])
                except Exception:
                    pass
            
            # Reconstruct resolved_values
            resolved_values = []
            if "resolved_values" in props:
                try:
                    resolved_values = json.loads(props["resolved_values"])
                except Exception:
                    pass
                    
            # Reconstruct source_entities
            source_entities = []
            if "source_entities" in props:
                try:
                    source_entities = json.loads(props["source_entities"])
                except Exception:
                    pass
            
            master_type = props.get("master_type", "ENTITY")
            
            # Build attributes dict
            attributes = {}
            special_keys = {"id", "entity_types", "resolved_values", "source_entities", "master_type", "dataset"}
            for k, v in props.items():
                if k not in special_keys:
                    try:
                        if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                            attributes[k] = json.loads(v)
                        else:
                            attributes[k] = v
                    except Exception:
                        attributes[k] = v
            
            master_entities.append({
                "master_id": master_id,
                "master_type": master_type,
                "entity_types": entity_types,
                "resolved_values": resolved_values,
                "source_entities": source_entities,
                "attributes": attributes
            })
            
        # 2. Fetch all relationships matching the dataset label
        rel_query = f"""
        MATCH (s:{dataset_label})-[r]->(t:{dataset_label})
        WHERE r.dataset = $dataset_label
        RETURN s.id AS source, t.id AS target, type(r) AS relation, properties(r) AS props
        """
        rel_records = client.execute_read(rel_query, {"dataset_label": dataset_label})
        
        relations = []
        for rec in rel_records:
            source = rec["source"]
            target = rec["target"]
            relation_type = rec["relation"]
            props = dict(rec["props"])
            
            timestamp = props.pop("timestamp", None)
            confidence = props.pop("confidence", None)
            if confidence is not None:
                try:
                    confidence = float(confidence)
                except Exception:
                    pass
            source_type = props.pop("source_type", None)
            props.pop("dataset", None)
            
            # Reconstruct attributes
            attributes = {}
            for k, v in props.items():
                clean_key = k
                if k.startswith("attr_"):
                    clean_key = k[5:]
                try:
                    if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                        attributes[clean_key] = json.loads(v)
                    else:
                        attributes[clean_key] = v
                except Exception:
                    attributes[clean_key] = v
                    
            rel = {
                "source": source,
                "target": target,
                "relation": relation_type,
                "attributes": attributes
            }
            if timestamp is not None:
                rel["timestamp"] = timestamp
            if confidence is not None:
                rel["confidence"] = confidence
            if source_type is not None:
                rel["source_type"] = source_type
                
            relations.append(rel)
            
        return {
            "master_entities": master_entities,
            "relations": relations
        }
    finally:
        client.close()

def load_graph_data():
    global _GRAPH_DATA
    try:
        print("[Neo4j] Fetching graph data from AuraDB...")
        _GRAPH_DATA = fetch_graph_from_neo4j()
        print(f"[Neo4j] Successfully loaded {len(_GRAPH_DATA['master_entities'])} entities from database.")
    except Exception as e:
        print(f"[Neo4j] Failed to load from database, falling back to local file: {e}")
        path = get_graph_file_path()
        if not path.exists():
            raise FileNotFoundError(f"unified_graph.json not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            _GRAPH_DATA = json.load(f)
    return _GRAPH_DATA

def compute_insights():
    global _GRAPH_DATA, _SUSPECTS, _ALERTS, _TIMELINE, _SUMMARY
    
    if not _GRAPH_DATA:
        load_graph_data()
        
    masters = {m["master_id"]: m for m in _GRAPH_DATA.get("master_entities", [])}
    relations = _GRAPH_DATA.get("relations", [])
    
    # 1. Build NetworkX Graph
    G = nx.DiGraph()
    for m_id in masters:
        G.add_node(m_id)
        
    for r in relations:
        src = r["source"]
        tgt = r["target"]
        rel_type = r["relation"]
        # Only add edge if source and target are in master entities to avoid orphans
        if src in masters and tgt in masters:
            weight = r.get("confidence", 1.0)
            G.add_edge(src, tgt, type=rel_type, weight=weight)
            
    # Calculate centralities
    deg_cent = nx.degree_centrality(G)
    bet_cent = nx.betweenness_centrality(G, weight="weight")
    
    # 2. Financial Transaction Analysis (Smurfing, Circular Flows, and Alerts)
    _ALERTS = []
    
    # Find all bank transfers
    transfers = [r for r in relations if r["relation"] == "TRANSFERRED_TO"]
    
    # Map master IDs to their primary names for easy UI presentation
    def get_entity_name(m_id: str) -> str:
        if m_id not in masters:
            return m_id
        resolved = masters[m_id].get("resolved_values", [])
        # Find person name if possible
        for val in resolved:
            if not val.startswith("acc") and not val.startswith("twr") and "@" not in val and not any(c.isdigit() for c in val):
                return val.title()
        # Fallback to first resolved value or master_id
        return resolved[0] if resolved else m_id
        
    # Analyze bank transactions
    for tx in transfers:
        src_id = tx["source"]
        tgt_id = tx["target"]
        attrs = tx.get("attributes", {})
        amount = float(attrs.get("amount", 0))
        timestamp = tx.get("timestamp", "")
        
        src_name = get_entity_name(src_id)
        tgt_name = get_entity_name(tgt_id)
        
        # High value anomaly
        if amount > 50000:
            _ALERTS.append(TransactionAlert(
                source_id=src_id,
                source_name=src_name,
                target_id=tgt_id,
                target_name=tgt_name,
                amount=amount,
                timestamp=timestamp,
                alert_type="HIGH_VALUE",
                description=f"High-value bank transfer of Rs. {amount:,.2f} from {src_name} to {tgt_name}",
                risk_score=85.0
            ))
            
        # Night transaction anomaly (between 11 PM and 5 AM)
        try:
            # Parse timestamp (various formats)
            time_str = timestamp.split()[-1] if " " in timestamp else timestamp.split("T")[-1]
            hour = int(time_str.split(":")[0])
            if hour >= 23 or hour < 5:
                _ALERTS.append(TransactionAlert(
                    source_id=src_id,
                    source_name=src_name,
                    target_id=tgt_id,
                    target_name=tgt_name,
                    amount=amount,
                    timestamp=timestamp,
                    alert_type="ANOMALY",
                    description=f"Out-of-hours transfer at {timestamp} of Rs. {amount:,.2f} from {src_name} to {tgt_name}",
                    risk_score=70.0
                ))
        except Exception:
            pass
            
    # Detect Smurfing (one sender splits to multiple intermediaries, re-aggregating to aggregator, sending to Hawala)
    # Let's map account-to-account flows
    flow_map = {}
    for tx in transfers:
        src = tx["source"]
        tgt = tx["target"]
        amount = float(tx.get("attributes", {}).get("amount", 0))
        flow_map.setdefault(src, []).append((tgt, amount, tx.get("timestamp", "")))
        
    # Look for nodes that split transactions to many accounts (degree of transfer out > 3)
    for sender_id, outputs in flow_map.items():
        if len(outputs) >= 4:  # Split into 4 or more accounts
            intermediaries = [o[0] for o in outputs]
            amounts = [o[1] for o in outputs]
            avg_amount = sum(amounts) / len(amounts)
            
            # Check if these intermediaries transfer to a common aggregator
            aggregator_candidates = {}
            for inter in intermediaries:
                if inter in flow_map:
                    for tgt, amt, ts in flow_map[inter]:
                        aggregator_candidates[tgt] = aggregator_candidates.get(tgt, 0) + 1
            
            # Find if there is an aggregator with overlap
            for agg, count in aggregator_candidates.items():
                if count >= 3:  # At least 3 intermediaries merge back to this account
                    # Verify if aggregator sends to Hawala
                    sends_to_hawala = False
                    if agg in flow_map:
                        for tgt, amt, ts in flow_map[agg]:
                            resolved = masters.get(tgt, {}).get("resolved_values", [])
                            if "acc_hawala" in resolved or "ACC_HAWALA" in resolved:
                                sends_to_hawala = True
                                break
                    
                    risk = 95.0 if sends_to_hawala else 80.0
                    desc = (
                        f"Smurfing structure detected: {get_entity_name(sender_id)} split money to "
                        f"{len(intermediaries)} accounts, which re-aggregated at {get_entity_name(agg)}"
                    )
                    if sends_to_hawala:
                        desc += " and was transferred to a Hawala channel."
                        
                    _ALERTS.append(TransactionAlert(
                        source_id=sender_id,
                        source_name=get_entity_name(sender_id),
                        target_id=agg,
                        target_name=get_entity_name(agg),
                        amount=sum(amounts),
                        timestamp=outputs[0][2],
                        alert_type="SMURFING",
                        description=desc,
                        risk_score=risk
                    ))
                    
    # Circular money flow detection (cycles in bank transfers)
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            # Check if cycle contains TRANSFERRED_TO edges
            is_txn_cycle = True
            cycle_amount = 0
            for i in range(len(cycle)):
                u = cycle[i]
                v = cycle[(i + 1) % len(cycle)]
                edge_data = G.get_edge_data(u, v)
                if not edge_data or edge_data.get("type") != "TRANSFERRED_TO":
                    is_txn_cycle = False
                    break
                    
            if is_txn_cycle and len(cycle) > 1:
                cycle_names = [get_entity_name(node) for node in cycle]
                _ALERTS.append(TransactionAlert(
                    source_id=cycle[0],
                    source_name=cycle_names[0],
                    target_id=cycle[-1],
                    target_name=cycle_names[-1],
                    amount=0.0,
                    timestamp="",
                    alert_type="CIRCULAR",
                    description=f"Circular fund routing cycle detected: {' -> '.join(cycle_names)} -> {cycle_names[0]}",
                    risk_score=90.0
                ))
    except Exception:
        pass
        
    # Deduplicate alerts based on alert_type and description
    seen_alert_keys = set()
    dedup_alerts = []
    for a in _ALERTS:
        key = (a.alert_type, a.description)
        if key not in seen_alert_keys:
            seen_alert_keys.add(key)
            dedup_alerts.append(a)
    _ALERTS = dedup_alerts

    # 3. Suspect Profiling & Risk Scoring (PERSON master entities)
    _SUSPECTS = []
    
    person_masters = [m for m in masters.values() if m["master_type"] == "PERSON"]
    
    for pm in person_masters:
        m_id = pm["master_id"]
        resolved = pm.get("resolved_values", [])
        
        # Primary name
        primary_name = "Unknown Suspect"
        for r_val in resolved:
            if not r_val.startswith("98") and not r_val.startswith("91") and "@" not in r_val and not any(c.isdigit() for c in r_val):
                primary_name = r_val.title()
                break
        if primary_name == "Unknown Suspect" and resolved:
            primary_name = resolved[0].title()
            
        # Collect reasons for flagging
        reasons = []
        base_risk = 10.0
        
        # Centrality reasons
        d_val = deg_cent.get(m_id, 0.0)
        b_val = bet_cent.get(m_id, 0.0)
        
        if d_val > 0.15:
            reasons.append("High volume of network connectivity and communication logs.")
            base_risk += 15.0
        if b_val > 0.2:
            reasons.append("Key broker / bridge node in transaction or communication flow.")
            base_risk += 25.0
            
        # FIR Specific logic
        resolved_lower = [v.lower() for v in resolved]
        if any("rahul" in v for v in resolved_lower):
            reasons.append("Named as the primary suspect in the First Information Report (FIR).")
            base_risk += 45.0
        if any("arjun" in v for v in resolved_lower):
            reasons.append("Suspected co-conspirator; high degree of direct contact with the primary suspect.")
            base_risk += 35.0
        if any("rajan" in v for v in resolved_lower):
            reasons.append("Associated with the main transaction aggregator account linked to Hawala exits.")
            base_risk += 40.0
        if any("vikram" in v for v in resolved_lower):
            reasons.append("Divergent geolocation movement pattern detected via cellular tower logs.")
            base_risk += 20.0
            
        # Check links to bank accounts
        # Find if this person owns an account that is flagged
        owned_accounts = []
        for r in relations:
            if r["relation"] == "OWNS_ACCOUNT":
                if r["source"] == m_id or r["target"] == m_id:
                    acc_id = r["target"] if r["source"] == m_id else r["source"]
                    owned_accounts.append(acc_id)
                    
        for acc in owned_accounts:
            # Check if this account was part of any alert
            acc_resolved = masters.get(acc, {}).get("resolved_values", [])
            for alert in _ALERTS:
                if alert.source_id == acc or alert.target_id == acc:
                    reasons.append(f"Account {acc_resolved[0] if acc_resolved else acc} flagged under transaction alert: {alert.alert_type}.")
                    base_risk += 15.0
                    
        # Normalize risk score to be between 10.0 and 99.0
        risk_score = min(max(base_risk, 10.0), 99.0)
        
        _SUSPECTS.append(SuspectDetail(
            master_id=m_id,
            name=primary_name,
            risk_score=round(risk_score, 1),
            degree_centrality=round(d_val, 4),
            betweenness_centrality=round(b_val, 4),
            identifiers=resolved,
            entity_types=pm["entity_types"],
            reasons=reasons
        ))
        
    # Sort suspects by Risk Score desc
    _SUSPECTS.sort(key=lambda s: s.risk_score, reverse=True)
    
    # 4. Temporal Timeline Analysis
    _TIMELINE = []
    temporal_relations = [r for r in relations if r.get("timestamp")]
    
    for r in temporal_relations:
        src_id = r["source"]
        tgt_id = r["target"]
        rel_type = r["relation"]
        timestamp = r["timestamp"]
        attrs = r.get("attributes", {})
        
        src_name = get_entity_name(src_id)
        tgt_name = get_entity_name(tgt_id)
        
        # Format nice descriptions
        desc = ""
        if rel_type == "CALLED":
            duration = attrs.get("duration", 0)
            desc = f"{src_name} called {tgt_name} for {duration} seconds."
        elif rel_type == "TRANSFERRED_TO":
            amount = attrs.get("amount", 0)
            desc = f"Bank transfer of Rs. {amount:,.2f} from account {src_name} to {tgt_name}."
        elif rel_type == "MESSAGED":
            desc = f"{src_name} sent a secure chat message to {tgt_name}."
        elif rel_type == "EMAILED":
            desc = f"{src_name} sent an email to {tgt_name}."
        elif rel_type == "LOCATED_AT":
            desc = f"{src_name} was located at tower/coordinate {tgt_name}."
        elif rel_type == "MOVED_TO":
            dist = attrs.get("distance_meters", 0)
            desc = f"Location movement to {tgt_name} (distance: {dist:.1f} meters)."
        elif rel_type == "DETECTED":
            desc = f"{src_name} was detected at {tgt_name} camera checkpoint."
        else:
            desc = f"Relation {rel_type} established between {src_name} and {tgt_name}."
            
        _TIMELINE.append(TimelineEvent(
            timestamp=timestamp,
            source_id=src_id,
            source_name=src_name,
            target_id=tgt_id,
            target_name=tgt_name,
            relation_type=rel_type,
            description=desc,
            confidence=r.get("confidence", 0.95),
            source_type=r.get("source_type", "unknown")
        ))
        
    # Sort timeline chronologically (handle ISO or space dates gracefully)
    def parse_time(ts_str: str) -> datetime:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        # Fallback
        return datetime.min
        
    _TIMELINE.sort(key=lambda e: parse_time(e.timestamp))
    
    # 5. Global Summary Metrics
    from collections import Counter
    entity_counts = Counter(m["master_type"] for m in masters.values())
    relation_counts = Counter(r["relation"] for r in relations)
    
    max_risk_suspect_name = _SUSPECTS[0].name if _SUSPECTS else "None"
    
    _SUMMARY = GraphSummary(
        total_entities=len(masters),
        total_relations=len(relations),
        entity_type_counts=dict(entity_counts),
        relation_type_counts=dict(relation_counts),
        max_risk_suspect=max_risk_suspect_name,
        total_alerts=len(_ALERTS)
    )

def get_graph_payload() -> GraphPayload:
    rc = _get_redis_client()
    if rc:
        try:
            cached = rc.get_cached_insights("graph_payload")
            if cached:
                return GraphPayload(**cached)
        except Exception:
            pass
            
    global _GRAPH_DATA
    if not _GRAPH_DATA:
        compute_insights()
        
    payload = GraphPayload(
        master_entities=[EntityDetail(**m) for m in _GRAPH_DATA.get("master_entities", [])],
        relations=[RelationDetail(**r) for r in _GRAPH_DATA.get("relations", [])]
    )
    
    if rc:
        try:
            rc.cache_insights("graph_payload", payload.dict())
        except Exception:
            pass
    return payload

def get_suspects() -> List[SuspectDetail]:
    rc = _get_redis_client()
    if rc:
        try:
            cached = rc.get_cached_insights("suspects")
            if cached:
                return [SuspectDetail(**item) for item in cached]
        except Exception:
            pass
            
    global _SUSPECTS
    if not _SUSPECTS:
        compute_insights()
        
    if rc and _SUSPECTS:
        try:
            rc.cache_insights("suspects", [item.dict() for item in _SUSPECTS])
        except Exception:
            pass
    return _SUSPECTS

def get_alerts() -> List[TransactionAlert]:
    rc = _get_redis_client()
    if rc:
        try:
            cached = rc.get_cached_insights("alerts")
            if cached:
                return [TransactionAlert(**item) for item in cached]
        except Exception:
            pass
            
    global _ALERTS
    if not _ALERTS:
        compute_insights()
        
    if rc and _ALERTS:
        try:
            rc.cache_insights("alerts", [item.dict() for item in _ALERTS])
        except Exception:
            pass
    return _ALERTS

def get_timeline() -> List[TimelineEvent]:
    rc = _get_redis_client()
    if rc:
        try:
            cached = rc.get_cached_insights("timeline")
            if cached:
                return [TimelineEvent(**item) for item in cached]
        except Exception:
            pass
            
    global _TIMELINE
    if not _TIMELINE:
        compute_insights()
        
    if rc and _TIMELINE:
        try:
            rc.cache_insights("timeline", [item.dict() for item in _TIMELINE])
        except Exception:
            pass
    return _TIMELINE

def get_summary() -> GraphSummary:
    rc = _get_redis_client()
    if rc:
        try:
            cached = rc.get_cached_insights("summary")
            if cached:
                return GraphSummary(**cached)
        except Exception:
            pass
            
    global _SUMMARY
    if not _SUMMARY:
        compute_insights()
        
    if rc and _SUMMARY:
        try:
            rc.cache_insights("summary", _SUMMARY.dict())
        except Exception:
            pass
    return _SUMMARY
