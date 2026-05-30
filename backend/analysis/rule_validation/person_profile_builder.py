"""
person_profile_builder.py
===========================
Assembles and structures the final risk profile for each resolved person entity.
Extracts individual chronological timelines of suspicious events.
"""

from explanation_builder import build_person_explanation
from rule_engine import parse_timestamp, normalize_ts

def format_event_description(rel: dict, name_map: dict) -> str:
    """Creates a human-readable description of a relationship/event."""
    src = name_map.get(rel["source"], rel["source"])
    tgt = name_map.get(rel["target"], rel["target"])
    rel_type = rel.get("relation", "")
    attrs = rel.get("attributes", {})
    
    if rel_type == "CALLED":
        dur = attrs.get("duration", 0)
        ctype = attrs.get("call_type", "OUTGOING").lower()
        return f"{src} called {tgt} ({dur}s, {ctype})"
    elif rel_type == "MESSAGED":
        plat = attrs.get("platform", "chat")
        text = attrs.get("text", "")[:80]
        return f"{src} messaged {tgt} via {plat}: '{text}...'"
    elif rel_type == "EMAILED":
        subj = attrs.get("subject", "")[:80]
        return f"{src} emailed {tgt} -- Subject: {subj}"
    elif rel_type == "TRANSFERRED_TO":
        amt = attrs.get("amount", 0)
        ttype = attrs.get("transaction_type", "transfer")
        return f"{src} transferred Rs.{amt:,} to {tgt} via {ttype}"
    elif rel_type == "LOCATED_AT":
        return f"{src} observed located at {tgt}"
    elif rel_type == "MOVED_TO":
        return f"{src} moved to {tgt}"
    elif rel_type == "DETECTED":
        return f"{src} detected near {tgt}"
    elif rel_type == "POSTED_ON":
        content = attrs.get("content", "")[:80]
        return f"{src} posted on {tgt}: '{content}...'"
    else:
        return f"{src} linked to {tgt} via {rel_type}"

def build_person_timeline(person_id: str, relations: list, name_map: dict) -> list[dict]:
    """
    Collects, filters, and chronologically sorts all events/relations involving the person.
    """
    timeline_events = []
    
    for r in relations:
        if r["source"] == person_id or r["target"] == person_id:
            ts_str = r.get("timestamp", "")
            if not ts_str:
                continue
                
            ts = parse_timestamp(ts_str)
            if not ts:
                continue
                
            timeline_events.append({
                "timestamp": ts_str,
                "datetime": normalize_ts(ts),
                "action": r.get("relation", ""),
                "description": format_event_description(r, name_map),
                "confidence": r.get("confidence", 1.0),
                "source_type": r.get("source_type", "unknown")
            })
            
    # Sort chronologically
    timeline_events.sort(key=lambda x: x["datetime"])
    
    # Strip datetime objects before returning (not JSON serializable)
    for ev in timeline_events:
        ev.pop("datetime", None)
        
    return timeline_events

def build_person_profile(
    person_id: str,
    master: dict,
    name_map: dict,
    evidence: list,
    graph_metrics: dict,
    relations: list
) -> dict:
    """
    Constructs the complete, structured person risk profile.
    """
    name = name_map.get(person_id, person_id)
    identifiers = master.get("resolved_values", [])
    entity_types = master.get("entity_types", [])
    
    # Calculate average confidence of triggered evidence rules
    if evidence:
        avg_confidence = sum(e["confidence"] for e in evidence) / len(evidence)
    else:
        avg_confidence = 1.0
        
    # Get normalized risk score & risk level
    from risk_scorer import calculate_person_risk
    risk_score, risk_level = calculate_person_risk(person_id, evidence)
    
    # Get graph metrics
    metrics = graph_metrics.get(person_id, {"degree": 0.0, "betweenness": 0.0, "pagerank": 0.0})
    
    # Build timeline of events
    timeline = build_person_timeline(person_id, relations, name_map)
    
    # Build explanation
    explanation = build_person_explanation(name, risk_score, risk_level, evidence, avg_confidence)
    
    # Unique rule codes triggered
    rule_codes = sorted(list(set(e["rule_code"] for e in evidence)))
    
    return {
        "person_id": person_id,
        "name": name,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": float(round(avg_confidence, 2)),
        "graph_metrics": metrics,
        "triggered_rules": rule_codes,
        "explanation": explanation,
        "identifiers": identifiers,
        "entity_types": entity_types,
        "evidence": evidence,
        "timeline": timeline
    }
