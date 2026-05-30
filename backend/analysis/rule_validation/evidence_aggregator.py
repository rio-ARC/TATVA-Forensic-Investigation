"""
evidence_aggregator.py
========================
Processes and decorates triggered rule events with:
1. Source Reliability weights based on the data channel.
2. Exponential Time Decay based on event age.
3. Weighted risk contribution scores: Weight * Confidence * Reliability * Decay.
"""

import math
from datetime import datetime
from rule_engine import parse_timestamp, normalize_ts

# Define Source Reliability constants
SOURCE_RELIABILITY = {
    "bank_transaction": 1.0,
    "cdr_record": 1.0,
    "mobile_gps": 1.0,
    "telecom_tower": 1.0,
    "asset_tracker": 1.0,
    "vehicle_tracker": 1.0,
    "wearable_device": 1.0,
    "gps_analysis": 1.0,
    "fir_document": 0.9,
    "investigator_annotation": 0.9,
    "chat": 0.8,
    "emails": 0.8,
    "social": 0.8,
    "vehicle_camera": 0.8,
}

DEFAULT_RELIABILITY = 0.85
LAMBDA = 0.05 # 14-day half-life equivalent decay rate

def get_source_reliability(source_type: str) -> float:
    """Returns the reliability weight of a source type."""
    if not source_type:
        return DEFAULT_RELIABILITY
    return SOURCE_RELIABILITY.get(source_type.lower(), DEFAULT_RELIABILITY)

def calculate_time_decay(event_ts_str: str, max_ts: datetime) -> float:
    """
    Computes exp(-lambda * age_in_days) relative to the latest graph timestamp.
    Returns:
        float: Decay factor (0.0 to 1.0)
    """
    if not event_ts_str:
        return 1.0
        
    event_dt = parse_timestamp(event_ts_str)
    if not event_dt or not max_ts:
        return 1.0
        
    event_dt_norm = normalize_ts(event_dt)
    max_ts_norm = normalize_ts(max_ts)
    
    age_days = (max_ts_norm - event_dt_norm).total_seconds() / (24 * 3600)
    
    # If age is negative (event timestamp is in the future relative to max_ts, which shouldn't happen),
    # clamp it to 0
    if age_days < 0:
        age_days = 0.0
        
    return math.exp(-LAMBDA * age_days)

def aggregate_and_weight_evidence(triggers: list, max_graph_ts: datetime) -> list[dict]:
    """
    Decorates raw rule triggers with reliability, decay, and final weighted contribution scores.
    """
    decorated_triggers = []
    
    for t in triggers:
        weight = t.get("weight", 0.0)
        confidence = t.get("confidence", 1.0)
        
        # 1. Source Reliability
        source_type = t.get("source_type", "")
        reliability = get_source_reliability(source_type)
        
        # 2. Time Decay
        decay = calculate_time_decay(t.get("timestamp", ""), max_graph_ts)
        
        # 3. Weighted Contribution
        contribution = weight * confidence * reliability * decay
        
        decorated_triggers.append({
            "person_id": t["person_id"],
            "rule_code": t["rule_code"],
            "rule_name": t["rule_name"],
            "base_weight": weight,
            "confidence": float(round(confidence, 2)),
            "source_reliability": float(round(reliability, 2)),
            "time_decay": float(round(decay, 2)),
            "weighted_contribution": float(round(contribution, 2)),
            "timestamp": t.get("timestamp", ""),
            "evidence": t.get("evidence", {})
        })
        
    return decorated_triggers
