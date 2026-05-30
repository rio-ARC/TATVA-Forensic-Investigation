"""
rule_engine.py
================
Core Rule Engine layer for detecting single-type pattern violations
(Communication, Email, and keyword-based rules).
"""

from datetime import datetime, timedelta
from collections import defaultdict

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S+05:30",
]

def parse_timestamp(ts_str: str) -> datetime | None:
    """Try parsing a timestamp string with multiple known formats."""
    if not ts_str:
        return None
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except (ValueError, TypeError):
            continue
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None

def normalize_ts(dt: datetime) -> datetime:
    """Strip timezone info for safe comparison."""
    if dt and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

# ---------------------------------------------------------------------------
# Rule 1: Excessive Calling (> 50 outgoing calls in a single day)
# ---------------------------------------------------------------------------
def detect_excessive_calling(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    # Group outgoing calls by caller and date string
    calls_by_caller_date = defaultdict(list)
    
    for r in relations:
        if r.get("relation") == "CALLED":
            # Check if OUTGOING call
            attrs = r.get("attributes", {})
            call_type = attrs.get("call_type", "OUTGOING")
            if call_type != "OUTGOING":
                continue
                
            ts = parse_timestamp(r.get("timestamp", ""))
            if ts:
                ts_norm = normalize_ts(ts)
                date_str = ts_norm.strftime("%Y-%m-%d")
                calls_by_caller_date[(r["source"], date_str)].append((ts_norm, r))
                
    for (caller_id, date_str), calls in calls_by_caller_date.items():
        if len(calls) > 50:
            # We sort calls for timeline evidence
            calls.sort(key=lambda x: x[0])
            avg_confidence = sum(c[1].get("confidence", 1.0) for c in calls) / len(calls)
            
            triggers.append({
                "person_id": caller_id,
                "rule_code": "COMM_EXCESSIVE_CALLING",
                "rule_name": "Excessive Calling",
                "weight": 5.0,
                "confidence": avg_confidence,
                "source_type": "cdr_record",
                "timestamp": date_str + "T00:00:00",
                "evidence": {
                    "date": date_str,
                    "call_count": len(calls),
                    "recipients": list(set(name_map.get(c[1]["target"], c[1]["target"]) for c in calls)),
                    "descriptions": [f"Made outgoing call on {c[0].strftime('%H:%M:%S')} to {name_map.get(c[1]['target'], c[1]['target'])}" for c in calls[:5]]
                }
            })
    return triggers

# ---------------------------------------------------------------------------
# Rule 2: Call Burst (10+ calls within a 15-minute sliding window)
# ---------------------------------------------------------------------------
def detect_call_burst(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    # Group calls by participant (could be source or target)
    calls_by_person = defaultdict(list)
    
    for r in relations:
        if r.get("relation") == "CALLED":
            ts = parse_timestamp(r.get("timestamp", ""))
            if ts:
                ts_norm = normalize_ts(ts)
                calls_by_person[r["source"]].append((ts_norm, r))
                calls_by_person[r["target"]].append((ts_norm, r))
                
    for person_id, calls in calls_by_person.items():
        # Sort chronologically
        calls.sort(key=lambda x: x[0])
        
        # Sliding window
        for i in range(len(calls)):
            window_end = calls[i][0] + timedelta(minutes=15)
            cluster = [c for c in calls[i:] if c[0] <= window_end]
            
            if len(cluster) >= 10:
                avg_confidence = sum(c[1].get("confidence", 1.0) for c in cluster) / len(cluster)
                first_ts = cluster[0][0]
                last_ts = cluster[-1][0]
                
                triggers.append({
                    "person_id": person_id,
                    "rule_code": "COMM_CALL_BURST",
                    "rule_name": "Call Burst",
                    "weight": 8.0,
                    "confidence": avg_confidence,
                    "source_type": "cdr_record",
                    "timestamp": first_ts.isoformat(),
                    "evidence": {
                        "call_count": len(cluster),
                        "window_start": first_ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "window_end": last_ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "duration_minutes": int((last_ts - first_ts).total_seconds() / 60),
                        "partners": list(set(name_map.get(c[1]["target"] if c[1]["source"] == person_id else c[1]["source"], "?") for c in cluster))
                    }
                })
                break # trigger at most once per person to avoid duplicate burst flags
    return triggers

# ---------------------------------------------------------------------------
# Rule 3: Hub Communication (connected to > 20 unique phone number / master entities)
# ---------------------------------------------------------------------------
def detect_hub_communication(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    # Count unique targets of CALLED or MESSAGED relationships per source
    comm_partners = defaultdict(set)
    comm_relations = defaultdict(list)
    
    for r in relations:
        if r.get("relation") in ("CALLED", "MESSAGED"):
            src = r["source"]
            tgt = r["target"]
            comm_partners[src].add(tgt)
            comm_relations[src].append(r)
            
    for person_id, partners in comm_partners.items():
        if len(partners) > 20:
            rels = comm_relations[person_id]
            avg_confidence = sum(r.get("confidence", 1.0) for r in rels) / len(rels)
            timestamps = []
            for r in rels:
                ts = parse_timestamp(r.get("timestamp", ""))
                if ts:
                    timestamps.append(normalize_ts(ts))
            latest_ts = max(timestamps) if timestamps else None
            latest_ts_str = latest_ts.isoformat() if latest_ts else ""
            
            triggers.append({
                "person_id": person_id,
                "rule_code": "COMM_HUB",
                "rule_name": "Hub Communication",
                "weight": 10.0,
                "confidence": avg_confidence,
                "source_type": "cdr_record", # main source
                "timestamp": latest_ts_str,
                "evidence": {
                    "unique_partners_count": len(partners),
                    "partners": sorted([name_map.get(p, p) for p in partners])
                }
            })
    return triggers

# ---------------------------------------------------------------------------
# Rule 9: Deletion Language
# ---------------------------------------------------------------------------
def detect_deletion_language(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    for r in relations:
        attrs = r.get("attributes", {})
        text = (attrs.get("text", "") or attrs.get("subject", "") or "").lower()
        forensic = attrs.get("forensic_signals", {})
        
        # Trigger conditions
        has_signal = forensic.get("delete_instruction") is True
        has_keywords = any(kw in text for kw in ("delete this", "delete after", "delete message", "clear chat", "wipe our chat", "destroy evidence", "clear this chat"))
        
        if has_signal or has_keywords:
            ts = r.get("timestamp", "")
            channel = r.get("relation", "communication").lower()
            
            # Trigger for the sender of the deletion message
            triggers.append({
                "person_id": r["source"],
                "rule_code": "COMM_DELETION_LANGUAGE",
                "rule_name": "Deletion Language",
                "weight": 10.0,
                "confidence": r.get("confidence", 0.9),
                "source_type": r.get("source_type", "chat"),
                "timestamp": ts,
                "evidence": {
                    "channel": channel,
                    "target": name_map.get(r["target"], r["target"]),
                    "text_snippet": (attrs.get("text") or attrs.get("subject") or "")[:150],
                    "matched_by": "forensic_signal" if has_signal else "keyword_match"
                }
            })
    return triggers

# ---------------------------------------------------------------------------
# Rule 10: Money Request
# ---------------------------------------------------------------------------
def detect_money_request(relations: list, name_map: dict) -> list[dict]:
    triggers = []
    for r in relations:
        attrs = r.get("attributes", {})
        text = (attrs.get("text", "") or attrs.get("subject", "") or "").lower()
        forensic = attrs.get("forensic_signals", {})
        
        # Trigger conditions
        has_signal = forensic.get("has_money_ref") is True
        has_keywords = any(kw in text for kw in ("transfer", "withdraw", "account", "cash", "rupees", "rs.", "money", "payment"))
        
        if has_signal or has_keywords:
            ts = r.get("timestamp", "")
            channel = r.get("relation", "communication").lower()
            
            triggers.append({
                "person_id": r["source"],
                "rule_code": "COMM_MONEY_REQUEST",
                "rule_name": "Money Request",
                "weight": 15.0,
                "confidence": r.get("confidence", 0.95),
                "source_type": r.get("source_type", "chat"),
                "timestamp": ts,
                "evidence": {
                    "channel": channel,
                    "target": name_map.get(r["target"], r["target"]),
                    "text_snippet": (attrs.get("text") or attrs.get("subject") or "")[:150],
                    "matched_by": "forensic_signal" if has_signal else "keyword_match"
                }
            })
    return triggers

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run_rule_engine(relations: list, name_map: dict) -> list[dict]:
    all_triggers = []
    all_triggers.extend(detect_excessive_calling(relations, name_map))
    all_triggers.extend(detect_call_burst(relations, name_map))
    all_triggers.extend(detect_hub_communication(relations, name_map))
    all_triggers.extend(detect_deletion_language(relations, name_map))
    all_triggers.extend(detect_money_request(relations, name_map))
    return all_triggers
