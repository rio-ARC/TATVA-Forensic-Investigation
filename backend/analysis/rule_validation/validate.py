"""
validate.py
=============
Main orchestrator for the Risk Intelligence Engine.
Loads the unified graph, runs all 10 rules and temporal analyzers,
computes confidence-weighted and time-decayed risk scores,
and generates person_risk_profiles.json, relationship_risk_profiles.json,
alerts.json, and backward-compatible flags.json.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Ensure packages can be imported
CURRENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CURRENT_DIR.parent.parent))
sys.path.insert(0, str(CURRENT_DIR))

# Import modular components
from rule_engine import run_rule_engine, parse_timestamp, normalize_ts
from graph_metrics import compute_graph_metrics
from temporal_analyzer import run_temporal_analysis, get_colocations
from evidence_aggregator import aggregate_and_weight_evidence
from person_profile_builder import build_person_profile
from relationship_profile_builder import build_relationship_profiles

# Configuration
GRAPH_PATH = CURRENT_DIR.parent.parent / "Graph_Integration_Layer" / "output" / "unified_graph.json"
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PERSON_PROFILES_OUT = OUTPUT_DIR / "person_risk_profiles.json"
RELATIONSHIP_PROFILES_OUT = OUTPUT_DIR / "relationship_risk_profiles.json"
FLAGS_OUT = OUTPUT_DIR / "flags.json"
ALERTS_OUT = OUTPUT_DIR / "alerts.json"

# Neo4j integration
try:
    from db_helper.dp_helper import get_graph_data_from_neo4j, is_neo4j_available
    _NEO4J_IMPORTED = True
except ImportError:
    _NEO4J_IMPORTED = False

def load_graph() -> dict:
    """Load graph data. Priority: Neo4j AuraDB -> unified_graph.json (fallback)."""
    if _NEO4J_IMPORTED and is_neo4j_available():
        try:
            print("[validate] Using Neo4j as data source.")
            return get_graph_data_from_neo4j()
        except Exception as e:
            print(f"[validate] Neo4j failed ({e}), falling back to JSON.")
    print("[validate] Using unified_graph.json (fallback).")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_entity_name(master: dict) -> str:
    """Extract the best human-readable name for a master entity."""
    resolved = master.get("resolved_values", [])
    entity_types = master.get("entity_types", [])
    master_type = master.get("master_type", "")

    if master_type == "PERSON" or "PERSON" in entity_types:
        for val in resolved:
            if not val:
                continue
            if val.startswith("acc") or val.startswith("android_") or val.startswith("watch_"):
                continue
            if val.replace(" ", "").isdigit():
                continue
            if val.startswith("@"):
                continue
            if "\n" in val or len(val) > 50:
                continue
            return val.title()

    for val in resolved:
        if val and "\n" not in val and len(val) < 80:
            if master_type == "ENTITY" and val.startswith("acc"):
                return val.upper()
            return val.title()

    return master.get("master_id", "Unknown")

# ---------------------------------------------------------------------------
# Extra Rules Implemented in Orchestrator for direct access to context
# ---------------------------------------------------------------------------

# Rule 5: Smurfing (3+ transfers under 10,000 INR in 30 mins)
def detect_smurfing_triggers(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    transfers = [r for r in relations if r.get("relation") == "TRANSFERRED_TO"]
    by_source = defaultdict(list)
    for t in transfers:
        by_source[t["source"]].append(t)
        
    for source_id, txns in by_source.items():
        if len(txns) < 3:
            continue
            
        timed = []
        for t in txns:
            ts = parse_timestamp(t.get("timestamp", ""))
            if ts:
                timed.append((normalize_ts(ts), t))
        timed.sort(key=lambda x: x[0])
        
        for i in range(len(timed)):
            window_end = timed[i][0] + timedelta(minutes=30)
            cluster = [x for x in timed[i:] if x[0] <= window_end]
            
            if len(cluster) < 3:
                continue
                
            amounts = [x[1].get("attributes", {}).get("amount", 0) for x in cluster]
            if all(a < 10000 for a in amounts):
                total = sum(amounts)
                first_ts = cluster[0][0]
                
                triggers.append({
                    "person_id": source_id,
                    "rule_code": "FIN_SMURFING",
                    "rule_name": "Smurfing",
                    "weight": 15.0,
                    "confidence": sum(x[1].get("confidence", 1.0) for x in cluster) / len(cluster),
                    "source_type": "bank_transaction",
                    "timestamp": first_ts.isoformat(),
                    "evidence": {
                        "transfer_count": len(cluster),
                        "total_amount": total,
                        "amounts": amounts,
                        "targets": [name_map.get(x[1]["target"], x[1]["target"]) for x in cluster]
                    }
                })
                break
    return triggers

# Rule 6: High Velocity (10+ transfers in 30 mins)
def detect_high_velocity(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    transfers = [r for r in relations if r.get("relation") == "TRANSFERRED_TO"]
    by_account = defaultdict(list)
    for t in transfers:
        by_account[t["source"]].append(t)
        by_account[t["target"]].append(t)
        
    for acc_id, txns in by_account.items():
        if len(txns) < 10:
            continue
            
        timed = []
        for t in txns:
            ts = parse_timestamp(t.get("timestamp", ""))
            if ts:
                timed.append((normalize_ts(ts), t))
        timed.sort(key=lambda x: x[0])
        
        for i in range(len(timed)):
            window_end = timed[i][0] + timedelta(minutes=30)
            cluster = [x for x in timed[i:] if x[0] <= window_end]
            
            if len(cluster) >= 10:
                first_ts = cluster[0][0]
                triggers.append({
                    "person_id": acc_id,
                    "rule_code": "FIN_HIGH_VELOCITY",
                    "rule_name": "High Velocity Transactions",
                    "weight": 10.0,
                    "confidence": sum(x[1].get("confidence", 1.0) for x in cluster) / len(cluster),
                    "source_type": "bank_transaction",
                    "timestamp": first_ts.isoformat(),
                    "evidence": {
                        "transaction_count": len(cluster),
                        "window_start": first_ts.isoformat()
                    }
                })
                break
    return triggers

# Rule 7: Suspicious Co-location (Co-location with a known suspect (Rahul Sen) within 15 mins)
def detect_suspicious_colocation(relations: list, masters: dict, name_map: dict) -> list[dict]:
    triggers = []
    colocations = get_colocations(relations, masters)
    
    # Identify Rahul Sen ID
    rahul_ids = set()
    for mid, m in masters.items():
        r_vals = [v.lower() for v in m.get("resolved_values", [])]
        if any("rahul" in v for v in r_vals):
            rahul_ids.add(mid)
            
    for coloc in colocations:
        p_a = coloc["person_a"]
        p_b = coloc["person_b"]
        
        # Check if one of them is Rahul
        if p_a in rahul_ids and p_b not in rahul_ids:
            triggers.append({
                "person_id": p_b,
                "rule_code": "GPS_SUSPICIOUS_COLOCATION",
                "rule_name": "Suspicious Co-location",
                "weight": 12.0,
                "confidence": coloc["confidence"],
                "source_type": coloc["source_type"],
                "timestamp": coloc["timestamp"].isoformat(),
                "evidence": {
                    "suspect": name_map.get(p_a, p_a),
                    "location": name_map.get(coloc["location_id"], coloc["location_id"]),
                    "timestamp": coloc["timestamp"].isoformat()
                }
            })
        elif p_b in rahul_ids and p_a not in rahul_ids:
            triggers.append({
                "person_id": p_a,
                "rule_code": "GPS_SUSPICIOUS_COLOCATION",
                "rule_name": "Suspicious Co-location",
                "weight": 12.0,
                "confidence": coloc["confidence"],
                "source_type": coloc["source_type"],
                "timestamp": coloc["timestamp"].isoformat(),
                "evidence": {
                    "suspect": name_map.get(p_b, p_b),
                    "location": name_map.get(coloc["location_id"], coloc["location_id"]),
                    "timestamp": coloc["timestamp"].isoformat()
                }
            })
    return triggers

# Rule 8: Frequent Visits (3+ visits by a person to the same location)
def detect_frequent_visits(relations: list, masters: dict, name_map: dict) -> list[dict]:
    triggers = []
    location_visits = defaultdict(list)
    
    for r in relations:
        if r.get("relation") == "LOCATED_AT":
            person_id = r["source"]
            loc_id = r["target"]
            ts = parse_timestamp(r.get("timestamp", ""))
            
            if ts and person_id in masters and masters[person_id].get("master_type") == "PERSON":
                location_visits[(person_id, loc_id)].append(normalize_ts(ts))
                
    for (person_id, loc_id), timestamps in location_visits.items():
        # Keep unique dates or distinct hours to filter duplicate pings
        unique_visits = sorted(list(set(timestamps)))
        
        # Filter pings within 10 minutes to count as distinct visits
        distinct_visits = []
        for v in unique_visits:
            if not distinct_visits or (v - distinct_visits[-1]).total_seconds() > 10 * 60:
                distinct_visits.append(v)
                
        if len(distinct_visits) >= 3:
            triggers.append({
                "person_id": person_id,
                "rule_code": "GPS_FREQUENT_VISITS",
                "rule_name": "Frequent Visits",
                "weight": 8.0,
                "confidence": 0.95,
                "source_type": "gps_analysis",
                "timestamp": distinct_visits[-1].isoformat(),
                "evidence": {
                    "location": name_map.get(loc_id, loc_id),
                    "visit_count": len(distinct_visits),
                    "visit_times": [v.isoformat() for v in distinct_visits]
                }
            })
    return triggers

# Rule 11: Cross-source Corroboration (3+ distinct raw data source types)
def detect_cross_source_corroboration(relations: list, masters: dict, name_map: dict) -> list[dict]:
    entity_sources = defaultdict(set)
    for r in relations:
        st = r.get("source_type", "")
        if not st:
            prov = r.get("provenance", "")
            if prov:
                st = prov.split(":")[0].replace(".txt", "").replace(".json", "")
        if not st:
            continue
            
        for eid in [r.get("source"), r.get("target")]:
            if eid:
                entity_sources[eid].add(st)
                
    triggers = []
    for entity_id, sources in entity_sources.items():
        if len(sources) >= 3:
            # Trigger corroboration
            timestamps = []
            for r in relations:
                if r["source"] == entity_id or r["target"] == entity_id:
                    ts = parse_timestamp(r.get("timestamp", ""))
                    if ts:
                        timestamps.append(normalize_ts(ts))
            latest_ts = max(timestamps) if timestamps else None
            latest_ts_str = latest_ts.isoformat() if latest_ts else ""
            
            triggers.append({
                "person_id": entity_id,
                "rule_code": "CO_CORROBORATION",
                "rule_name": "Cross-Source Corroboration",
                "weight": 10.0,
                "confidence": 1.0,
                "source_type": "investigator_annotation",
                "timestamp": latest_ts_str,
                "evidence": {
                    "sources_count": len(sources),
                    "sources_list": sorted(list(sources))
                }
            })
    return triggers


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------
def run_validation_pipeline() -> dict:
    print("[validate] Starting Risk Intelligence calculation pipeline...")
    
    # 1. Load Graph Data
    graph = load_graph()
    relations = graph.get("relations", [])
    master_entities = graph.get("master_entities", [])
    
    # Build maps
    masters_dict = {m["master_id"]: m for m in master_entities}
    name_map = {m["master_id"]: get_entity_name(m) for m in master_entities}
    
    # Find latest timestamp in graph for Time Decay calculations
    max_ts = datetime.min
    for r in relations:
        ts = parse_timestamp(r.get("timestamp", ""))
        if ts:
            ts_norm = normalize_ts(ts)
            if ts_norm > max_ts:
                max_ts = ts_norm
    if max_ts == datetime.min:
        max_ts = datetime.now()
    print(f"[validate] Reference timeline maximum timestamp: {max_ts.isoformat()}")
    
    # 2. Run rule engine (Rule 1, 2, 3, 9, 10)
    rule_triggers = run_rule_engine(relations, name_map)
    print(f"[validate]   Core rules triggered: {len(rule_triggers)}")
    
    # 3. Run temporal analyzer (Rule 4, Comm->Tx, GPS->Tx, Email->Call->Tx)
    temporal_triggers = run_temporal_analysis(relations, masters_dict, name_map)
    print(f"[validate]   Temporal sequences triggered: {len(temporal_triggers)}")
    
    # 4. Run additional rules (Rule 5, 6, 7, 8, 11)
    smurfing_triggers = detect_smurfing_triggers(relations, name_map)
    hv_triggers = detect_high_velocity(relations, name_map)
    coloc_triggers = detect_suspicious_colocation(relations, masters_dict, name_map)
    frequent_triggers = detect_frequent_visits(relations, masters_dict, name_map)
    corrob_triggers = detect_cross_source_corroboration(relations, masters_dict, name_map)
    print(f"[validate]   Smurfing / velocity triggers: {len(smurfing_triggers) + len(hv_triggers)}")
    print(f"[validate]   GPS co-location / visit triggers: {len(coloc_triggers) + len(frequent_triggers)}")
    print(f"[validate]   Corroboration triggers: {len(corrob_triggers)}")
    
    # Combine all triggers
    all_raw_triggers = (
        rule_triggers + temporal_triggers + smurfing_triggers + 
        hv_triggers + coloc_triggers + frequent_triggers + corrob_triggers
    )
    
    # 5. Aggregate and Weight Evidence (Confidence & Time Decay)
    weighted_triggers = aggregate_and_weight_evidence(all_raw_triggers, max_ts)
    print(f"[validate] Decorated and weighted {len(weighted_triggers)} total evidence items.")
    
    # Group weighted evidence by person/entity ID
    evidence_by_person = defaultdict(list)
    for wt in weighted_triggers:
        evidence_by_person[wt["person_id"]].append(wt)
        
    # 6. Compute Network Centrality Metrics
    graph_metrics = compute_graph_metrics(master_entities, relations)
    print(f"[validate] Calculated centrality metrics for {len(graph_metrics)} entities.")
    
    # 7. Build Person Profiles (only for master_type == PERSON)
    person_profiles = []
    for master in master_entities:
        mid = master["master_id"]
        # Include if type is PERSON or is associated with evidence
        if master.get("master_type") == "PERSON" or mid in evidence_by_person:
            # Get evidence
            pe_evidence = evidence_by_person.get(mid, [])
            profile = build_person_profile(mid, master, name_map, pe_evidence, graph_metrics, relations)
            person_profiles.append(profile)
            
    # Sort person profiles by risk score descending
    person_profiles.sort(key=lambda x: x["risk_score"], reverse=True)
    print(f"[validate] Generated {len(person_profiles)} person risk profiles.")
    
    # 8. Build Relationship Profiles
    relationship_profiles = build_relationship_profiles(relations, masters_dict, name_map)
    print(f"[validate] Generated {len(relationship_profiles)} relationship risk profiles.")
    
    # Save Outputs
    # A. Save person risk profiles
    with open(PERSON_PROFILES_OUT, "w", encoding="utf-8") as f:
        json.dump(person_profiles, f, indent=2, ensure_ascii=False)
    print(f"[validate] Saved person profiles to {PERSON_PROFILES_OUT.name}")
    
    # B. Save relationship profiles
    with open(RELATIONSHIP_PROFILES_OUT, "w", encoding="utf-8") as f:
        json.dump(relationship_profiles, f, indent=2, ensure_ascii=False)
    print(f"[validate] Saved relationship profiles to {RELATIONSHIP_PROFILES_OUT.name}")
    
    # C. Save alerts.json (Simplified list of alerts/triggers for easy consumption)
    alerts_data = []
    for wt in weighted_triggers:
        alerts_data.append({
            "entity_id": wt["person_id"],
            "entity_name": name_map.get(wt["person_id"], wt["person_id"]),
            "rule": wt["rule_code"],
            "description": wt["rule_name"],
            "weighted_score": wt["weighted_contribution"],
            "timestamp": wt["timestamp"],
            "evidence": wt["evidence"]
        })
    with open(ALERTS_OUT, "w", encoding="utf-8") as f:
        json.dump(alerts_data, f, indent=2, ensure_ascii=False)
    print(f"[validate] Saved alerts listing to {ALERTS_OUT.name}")
    
    # D. Save backward-compatible flags.json
    legacy_flags = compile_legacy_flags(weighted_triggers, name_map, masters_dict)
    with open(FLAGS_OUT, "w", encoding="utf-8") as f:
        json.dump(legacy_flags, f, indent=2, ensure_ascii=False)
    print(f"[validate] Saved backward-compatible flags to {FLAGS_OUT.name}")
    
    return {
        "status": "success",
        "person_profiles_count": len(person_profiles),
        "relationship_profiles_count": len(relationship_profiles)
    }

def compile_legacy_flags(weighted_triggers: list, name_map: dict, masters: dict) -> dict:
    """
    Groups and formats the decorated triggers into the legacy flags.json schema structure:
    - smurfing
    - forensic_hits
    - communication_bursts
    - colocations
    - cross_source_corroboration
    """
    smurfing_list = []
    forensic_hits_list = []
    comm_bursts_list = []
    colocations_list = []
    corrob_list = []
    
    for wt in weighted_triggers:
        code = wt["rule_code"]
        score = wt["weighted_contribution"]
        
        # Map score to legacy severity (CRITICAL, HIGH, MEDIUM)
        if score >= 15.0:
            severity = "CRITICAL"
        elif score >= 8.0:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
            
        evidence = wt["evidence"]
        person_id = wt["person_id"]
        name = name_map.get(person_id, person_id)
        
        if code in ("FIN_SMURFING", "FIN_MULE_PATTERN", "FIN_HIGH_VELOCITY"):
            smurfing_list.append({
                "rule": "SMURFING_DETECTED" if code == "FIN_SMURFING" else code,
                "severity": severity,
                "account_id": person_id,
                "account_name": name,
                "recipients": evidence.get("targets", [evidence.get("outbound_transfer", {}).get("target", "Unknown")]),
                "recipient_ids": [], # filled as empty
                "amounts": evidence.get("amounts", [evidence.get("outbound_transfer", {}).get("amount", 0)]),
                "total_amount": evidence.get("total_amount", evidence.get("outbound_transfer", {}).get("amount", 0)),
                "transfer_count": evidence.get("transfer_count", 1),
                "time_window": wt["timestamp"],
                "duration_minutes": evidence.get("delay_seconds", 0) // 60,
                "description": f"Flagged financial behavior ({wt['rule_name']}): score contribution {score}"
            })
            
        elif code in ("COMM_DELETION_LANGUAGE", "COMM_MONEY_REQUEST"):
            forensic_hits_list.append({
                "rule": "FORENSIC_HIT",
                "severity": severity,
                "channel": evidence.get("channel", "chat"),
                "source": name,
                "source_id": person_id,
                "target": evidence.get("target", "Unknown"),
                "target_id": "",
                "signal": "delete_instruction" if code == "COMM_DELETION_LANGUAGE" else "has_money_ref",
                "timestamp": wt["timestamp"],
                "text_snippet": evidence.get("text_snippet", ""),
                "description": f"Forensic hit ({wt['rule_name']}): {evidence.get('text_snippet', '')}"
            })
            
        elif code in ("COMM_EXCESSIVE_CALLING", "COMM_CALL_BURST", "COMM_HUB", "TEMP_COMM_TO_TRANSFER", "TEMP_EMAIL_CALL_TRANSFER"):
            comm_bursts_list.append({
                "rule": "COMMUNICATION_BURST" if code == "COMM_CALL_BURST" else code,
                "severity": severity,
                "actors": [name, "Network Target"],
                "actor_ids": [person_id],
                "count": evidence.get("call_count", evidence.get("unique_partners_count", 1)),
                "window": wt["timestamp"],
                "description": f"Communication pattern ({wt['rule_name']}) flagged: score contribution {score}"
            })
            
        elif code in ("GPS_SUSPICIOUS_COLOCATION", "GPS_FREQUENT_VISITS", "TEMP_COLOCATION_TO_TRANSFER"):
            colocations_list.append({
                "rule": "RENDEZVOUS" if code == "GPS_SUSPICIOUS_COLOCATION" else code,
                "severity": severity,
                "persons": [name, evidence.get("suspect", "Known Suspect")],
                "person_ids": [person_id],
                "location": evidence.get("location", "Unknown Location"),
                "location_id": "",
                "timestamps": [wt["timestamp"]],
                "description": f"Location activity ({wt['rule_name']}) observed at {evidence.get('location', '')}"
            })
            
        elif code == "CO_CORROBORATION":
            corrob_list.append({
                "rule": "CO_CORROBORATION",
                "severity": severity,
                "entity_name": name,
                "entity_id": person_id,
                "entity_type": masters.get(person_id, {}).get("master_type", "PERSON"),
                "sources": evidence.get("sources_list", []),
                "source_count": evidence.get("sources_count", 0),
                "description": f"Corroboration flag: appears across {evidence.get('sources_count', 0)} sources"
            })
            
    all_flags = {
        "smurfing": smurfing_list,
        "forensic_hits": forensic_hits_list,
        "communication_bursts": comm_bursts_list,
        "colocations": colocations_list,
        "cross_source_corroboration": corrob_list
    }
    
    total = sum(len(v) for v in all_flags.values())
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_flags": total,
        "severity_summary": {
            "CRITICAL": sum(1 for c in all_flags.values() for f in c if f.get("severity") == "CRITICAL"),
            "HIGH": sum(1 for c in all_flags.values() for f in c if f.get("severity") == "HIGH"),
            "MEDIUM": sum(1 for c in all_flags.values() for f in c if f.get("severity") == "MEDIUM"),
        },
        "flags": all_flags
    }

if __name__ == "__main__":
    run_validation_pipeline()
