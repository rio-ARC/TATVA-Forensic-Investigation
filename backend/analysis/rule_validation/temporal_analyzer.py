"""
temporal_analyzer.py
======================
Analyzes complex multi-event chronological sequences and chains:
1. Mule Pattern: Inbound transfer -> Outbound transfer (within 30 mins)
2. Communication -> Financial Transfer (within 15 mins)
3. GPS Co-location -> Transaction (within 30 mins)
4. Email -> Call -> Transaction (within 60 mins)
"""

from datetime import datetime, timedelta
from collections import defaultdict
from rule_engine import parse_timestamp, normalize_ts

# Helper: Find all co-location events in the graph (similar to old validate.py colocation rule)
def get_colocations(relations: list, masters: dict) -> list[dict]:
    location_visits = defaultdict(list)  # location_id -> [(person_id, datetime, relation_dict)]

    for rel in relations:
        if rel.get("relation") == "LOCATED_AT":
            person_id = rel["source"]
            location_id = rel["target"]
            ts = parse_timestamp(rel.get("timestamp", ""))
            if not ts:
                continue
                
            # Only consider PERSON or mobile/tracker entities
            person_master = masters.get(person_id, {})
            ptype = person_master.get("master_type", "")
            if ptype not in ("PERSON", "ENTITY"):
                continue
                
            location_visits[location_id].append((person_id, normalize_ts(ts), rel))

    colocations = []
    for location_id, visits in location_visits.items():
        if len(set(v[0] for v in visits)) < 2:
            continue
            
        visits.sort(key=lambda x: x[1])
        
        # Check all pairs for time overlap
        for i, (pid_a, ts_a, rel_a) in enumerate(visits):
            for j in range(i + 1, len(visits)):
                pid_b, ts_b, rel_b = visits[j]
                if pid_b == pid_a:
                    continue
                    
                # If they are within 15 minutes of each other
                time_diff = abs((ts_b - ts_a).total_seconds())
                if time_diff <= 15 * 60:
                    max_ts = max(ts_a, ts_b)
                    colocations.append({
                        "person_a": pid_a,
                        "person_b": pid_b,
                        "location_id": location_id,
                        "timestamp": max_ts,
                        "confidence": min(rel_a.get("confidence", 1.0), rel_b.get("confidence", 1.0)),
                        "source_type": rel_a.get("source_type", "gps_analysis")
                    })
    return colocations

# ---------------------------------------------------------------------------
# 1. Mule Pattern: Inbound transfer -> Outbound transfer (within 30 mins)
# ---------------------------------------------------------------------------
def detect_mule_patterns(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    transfers = [r for r in relations if r.get("relation") == "TRANSFERRED_TO"]
    
    # Group transfers by account
    inbound_transfers = defaultdict(list)  # target_acc -> [transfer_dict]
    outbound_transfers = defaultdict(list) # source_acc -> [transfer_dict]
    
    for t in transfers:
        ts = parse_timestamp(t.get("timestamp", ""))
        if ts:
            ts_norm = normalize_ts(ts)
            inbound_transfers[t["target"]].append((ts_norm, t))
            outbound_transfers[t["source"]].append((ts_norm, t))
            
    for acc_id, in_txns in inbound_transfers.items():
        out_txns = outbound_transfers.get(acc_id, [])
        if not out_txns:
            continue
            
        # Check for immediate forwarding
        for in_ts, in_t in in_txns:
            for out_ts, out_t in out_txns:
                # Outbound transfer must be after inbound, and within 30 minutes
                time_diff = (out_ts - in_ts).total_seconds()
                if 0 < time_diff <= 30 * 60:
                    # Trigger Mule Pattern
                    triggers.append({
                        "person_id": acc_id,
                        "rule_code": "FIN_MULE_PATTERN",
                        "rule_name": "Mule Pattern",
                        "weight": 20.0,
                        "confidence": min(in_t.get("confidence", 1.0), out_t.get("confidence", 1.0)),
                        "source_type": "bank_transaction",
                        "timestamp": out_ts.isoformat(),
                        "evidence": {
                            "inbound_transfer": {
                                "source": name_map.get(in_t["source"], in_t["source"]),
                                "amount": in_t.get("attributes", {}).get("amount", 0),
                                "timestamp": in_t.get("timestamp", "")
                            },
                            "outbound_transfer": {
                                "target": name_map.get(out_t["target"], out_t["target"]),
                                "amount": out_t.get("attributes", {}).get("amount", 0),
                                "timestamp": out_t.get("timestamp", "")
                            },
                            "delay_seconds": int(time_diff)
                        }
                    })
                    break # flag once per inbound-outbound pair
    return triggers

# ---------------------------------------------------------------------------
# 2. Communication -> Financial Transfer (within 15 mins)
# ---------------------------------------------------------------------------
def detect_comm_to_transfer(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    
    # Filter communications and transfers
    comms = []
    transfers = []
    
    for r in relations:
        ts = parse_timestamp(r.get("timestamp", ""))
        if not ts:
            continue
        ts_norm = normalize_ts(ts)
        
        if r.get("relation") in ("CALLED", "MESSAGED", "EMAILED"):
            comms.append((ts_norm, r))
        elif r.get("relation") == "TRANSFERRED_TO":
            transfers.append((ts_norm, r))
            
    # Check for comm followed by transfer within 15 minutes between same actors
    for comm_ts, comm in comms:
        c_src = comm["source"]
        c_tgt = comm["target"]
        
        for tx_ts, tx in transfers:
            # Transfer must occur after communication, and within 15 minutes
            time_diff = (tx_ts - comm_ts).total_seconds()
            if 0 <= time_diff <= 15 * 60:
                # Check if same participants are involved
                # E.g., A calls B, and A transfers to B, or B transfers to A, or A transfers to someone
                # Let's check if the transfer source is comm source, or transfer target is comm target, etc.
                is_related = (
                    (tx["source"] == c_src and tx["target"] == c_tgt) or
                    (tx["source"] == c_tgt and tx["target"] == c_src) or
                    (tx["source"] == c_src) or (tx["source"] == c_tgt)
                )
                if is_related:
                    triggers.append({
                        "person_id": c_src,
                        "rule_code": "TEMP_COMM_TO_TRANSFER",
                        "rule_name": "Communication -> Transfer Coordination",
                        "weight": 12.0,
                        "confidence": min(comm.get("confidence", 1.0), tx.get("confidence", 1.0)),
                        "source_type": tx.get("source_type", "bank_transaction"),
                        "timestamp": tx_ts.isoformat(),
                        "evidence": {
                            "communication": {
                                "type": comm["relation"],
                                "source": name_map.get(c_src, c_src),
                                "target": name_map.get(c_tgt, c_tgt),
                                "timestamp": comm.get("timestamp", "")
                            },
                            "transfer": {
                                "source": name_map.get(tx["source"], tx["source"]),
                                "target": name_map.get(tx["target"], tx["target"]),
                                "amount": tx.get("attributes", {}).get("amount", 0),
                                "timestamp": tx.get("timestamp", "")
                            },
                            "delay_seconds": int(time_diff)
                        }
                    })
                    break
    return triggers

# ---------------------------------------------------------------------------
# 3. GPS Co-location -> Transaction (within 30 mins)
# ---------------------------------------------------------------------------
def detect_colocation_to_transfer(
    relations: list, masters: dict, name_map: dict
) -> list[dict]:
    triggers = []
    colocations = get_colocations(relations, masters)
    transfers = [
        (normalize_ts(parse_timestamp(r.get("timestamp", ""))), r)
        for r in relations
        if r.get("relation") == "TRANSFERRED_TO" and parse_timestamp(r.get("timestamp", ""))
    ]
    
    for coloc in colocations:
        p_a = coloc["person_a"]
        p_b = coloc["person_b"]
        c_ts = coloc["timestamp"]
        
        for tx_ts, tx in transfers:
            # Transaction must occur after co-location, and within 30 minutes
            time_diff = (tx_ts - c_ts).total_seconds()
            if 0 <= time_diff <= 30 * 60:
                # Check if transaction involves either of the co-located persons
                if tx["source"] in (p_a, p_b) or tx["target"] in (p_a, p_b):
                    triggers.append({
                        "person_id": p_a, # flag both parties
                        "rule_code": "TEMP_COLOCATION_TO_TRANSFER",
                        "rule_name": "Rendezvous -> Money Transfer",
                        "weight": 15.0,
                        "confidence": min(coloc["confidence"], tx.get("confidence", 1.0)),
                        "source_type": "gps_analysis",
                        "timestamp": tx_ts.isoformat(),
                        "evidence": {
                            "location": name_map.get(coloc["location_id"], coloc["location_id"]),
                            "person_a": name_map.get(p_a, p_a),
                            "person_b": name_map.get(p_b, p_b),
                            "colocation_timestamp": c_ts.isoformat(),
                            "transfer": {
                                "source": name_map.get(tx["source"], tx["source"]),
                                "target": name_map.get(tx["target"], tx["target"]),
                                "amount": tx.get("attributes", {}).get("amount", 0),
                                "timestamp": tx.get("timestamp", "")
                            },
                            "delay_seconds": int(time_diff)
                        }
                    })
                    # Also flag person B
                    triggers.append({
                        "person_id": p_b,
                        "rule_code": "TEMP_COLOCATION_TO_TRANSFER",
                        "rule_name": "Rendezvous -> Money Transfer",
                        "weight": 15.0,
                        "confidence": min(coloc["confidence"], tx.get("confidence", 1.0)),
                        "source_type": "gps_analysis",
                        "timestamp": tx_ts.isoformat(),
                        "evidence": {
                            "location": name_map.get(coloc["location_id"], coloc["location_id"]),
                            "person_a": name_map.get(p_a, p_a),
                            "person_b": name_map.get(p_b, p_b),
                            "colocation_timestamp": c_ts.isoformat(),
                            "transfer": {
                                "source": name_map.get(tx["source"], tx["source"]),
                                "target": name_map.get(tx["target"], tx["target"]),
                                "amount": tx.get("attributes", {}).get("amount", 0),
                                "timestamp": tx.get("timestamp", "")
                            },
                            "delay_seconds": int(time_diff)
                        }
                    })
                    break
    return triggers

# ---------------------------------------------------------------------------
# 4. Email -> Call -> Transaction (within 60 mins)
# ---------------------------------------------------------------------------
def detect_email_call_transfer(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    
    emails = []
    calls = []
    transfers = []
    
    for r in relations:
        ts = parse_timestamp(r.get("timestamp", ""))
        if not ts:
            continue
        ts_norm = normalize_ts(ts)
        
        if r.get("relation") == "EMAILED":
            emails.append((ts_norm, r))
        elif r.get("relation") == "CALLED":
            calls.append((ts_norm, r))
        elif r.get("relation") == "TRANSFERRED_TO":
            transfers.append((ts_norm, r))
            
    # Check for Email -> Call -> Transfer chronologically in 60 mins
    for e_ts, email in emails:
        e_src = email["source"]
        e_tgt = email["target"]
        
        for c_ts, call in calls:
            # Call must be after email
            if c_ts < e_ts:
                continue
                
            # Check if call involves same actors
            c_actors = {call["source"], call["target"]}
            if not (e_src in c_actors or e_tgt in c_actors):
                continue
                
            for tx_ts, tx in transfers:
                # Transfer must be after call and within 60 minutes of email
                if tx_ts < c_ts:
                    continue
                time_diff = (tx_ts - e_ts).total_seconds()
                if time_diff <= 60 * 60:
                    # Check if transfer involves email actors
                    tx_actors = {tx["source"], tx["target"]}
                    if e_src in tx_actors or e_tgt in tx_actors:
                        triggers.append({
                            "person_id": e_src,
                            "rule_code": "TEMP_EMAIL_CALL_TRANSFER",
                            "rule_name": "Email -> Call -> Transfer Chain",
                            "weight": 18.0,
                            "confidence": min(email.get("confidence", 1.0), call.get("confidence", 1.0), tx.get("confidence", 1.0)),
                            "source_type": "emails",
                            "timestamp": tx_ts.isoformat(),
                            "evidence": {
                                "email": {
                                    "source": name_map.get(e_src, e_src),
                                    "target": name_map.get(e_tgt, e_tgt),
                                    "timestamp": email.get("timestamp", "")
                                },
                                "call": {
                                    "source": name_map.get(call["source"], call["source"]),
                                    "target": name_map.get(call["target"], call["target"]),
                                    "timestamp": call.get("timestamp", "")
                                },
                                "transfer": {
                                    "source": name_map.get(tx["source"], tx["source"]),
                                    "target": name_map.get(tx["target"], tx["target"]),
                                    "amount": tx.get("attributes", {}).get("amount", 0),
                                    "timestamp": tx.get("timestamp", "")
                                },
                                "span_seconds": int(time_diff)
                            }
                        })
                        break
    return triggers

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run_temporal_analysis(
    relations: list, masters: dict, name_map: dict
) -> list[dict]:
    triggers = []
    triggers.extend(detect_mule_patterns(relations, name_map))
    triggers.extend(detect_comm_to_transfer(relations, name_map))
    triggers.extend(detect_colocation_to_transfer(relations, masters, name_map))
    triggers.extend(detect_email_call_transfer(relations, name_map))
    return triggers
