"""
risk_scorer.py
================
Performs normalizations, assigns risk levels, and calculates risk scores
for both persons and relationships.
"""

from collections import defaultdict
from evidence_aggregator import get_source_reliability

# Saturation thresholds
PERSON_SATURATION_CAP = 60.0
RELATIONSHIP_SATURATION_CAP = 50.0

def assign_risk_level(score: float) -> str:
    """Assigns the risk level category based on the normalized risk score."""
    if score >= 80.0:
        return "CRITICAL"
    elif score >= 50.0:
        return "HIGH"
    elif score >= 25.0:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_person_risk(person_id: str, person_evidence: list) -> tuple[float, str]:
    """
    Computes normalized risk score and assigns a risk level for a person.
    """
    if not person_evidence:
        return 0.0, "LOW"
        
    sum_contributions = sum(e["weighted_contribution"] for e in person_evidence)
    normalized_score = min(100.0, (sum_contributions / PERSON_SATURATION_CAP) * 100.0)
    normalized_score = round(normalized_score, 1)
    
    return normalized_score, assign_risk_level(normalized_score)

def compute_relationship_risk_profiles(relations: list, masters: dict, name_map: dict) -> list[dict]:
    """
    Calculates relationship risk scores between pairs of master entities.
    Evaluates:
      - Call interactions (CALLED)
      - Message/Email interactions (MESSAGED, EMAILED)
      - Financial transfers (TRANSFERRED_TO)
      - Shared GPS locations (colocations)
      - Shared device / vehicle connectivity
    """
    # Key interaction pairs: sorted tuple (master_id_1, master_id_2) -> interaction data list
    pair_details = defaultdict(lambda: {
        "calls": [], "messages": [], "transfers": [], "colocations": [], "shared_devices": []
    })
    
    # 1. Evaluate Direct interactions
    for r in relations:
        src = r["source"]
        tgt = r["target"]
        rel_type = r.get("relation", "")
        conf = r.get("confidence", 1.0)
        source_type = r.get("source_type", "")
        reliability = get_source_reliability(source_type)
        ts = r.get("timestamp", "")
        
        pair = tuple(sorted([src, tgt]))
        
        # We only care about relationships between PERSON entities or PERSON <-> ACCOUNT/DEVICE
        src_type = masters.get(src, {}).get("master_type", "")
        tgt_type = masters.get(tgt, {}).get("master_type", "")
        
        if rel_type == "CALLED":
            pair_details[pair]["calls"].append({"confidence": conf, "reliability": reliability, "timestamp": ts})
        elif rel_type in ("MESSAGED", "EMAILED"):
            pair_details[pair]["messages"].append({"confidence": conf, "reliability": reliability, "timestamp": ts})
        elif rel_type == "TRANSFERRED_TO":
            amount = r.get("attributes", {}).get("amount", 0)
            pair_details[pair]["transfers"].append({"confidence": conf, "reliability": reliability, "timestamp": ts, "amount": amount})
            
    # 2. Check for shared device connectivity
    # E.g., if Person A owns Device D, and Person B owns Device D or uses it
    # E.g., A -> OWNS_ACCOUNT -> Acc1, B -> OWNS_ACCOUNT -> Acc1
    # Let's count shared resources
    resource_owners = defaultdict(set)
    for r in relations:
        if r.get("relation") in ("OWNS_ACCOUNT", "OWNS_DEVICE", "USED_DEVICE", "DETECTED"):
            # Group resource -> owners
            src = r["source"]
            tgt = r["target"]
            resource_owners[tgt].add(src)
            resource_owners[src].add(tgt)
            
    # If two entities share a resource, they are linked
    for resource, owners in resource_owners.items():
        owner_list = sorted(list(owners))
        if len(owner_list) >= 2:
            for i in range(len(owner_list)):
                for j in range(i + 1, len(owner_list)):
                    pair = (owner_list[i], owner_list[j])
                    pair_details[pair]["shared_devices"].append({
                        "resource": resource,
                        "resource_name": name_map.get(resource, resource),
                        "confidence": 1.0,
                        "reliability": 1.0
                    })

    # 3. Calculate scores for each pair
    relationship_profiles = []
    
    for pair, details in pair_details.items():
        ent1, ent2 = pair
        name1 = name_map.get(ent1, ent1)
        name2 = name_map.get(ent2, ent2)
        
        # Only profile relations involving at least one PERSON
        type1 = masters.get(ent1, {}).get("master_type", "")
        type2 = masters.get(ent2, {}).get("master_type", "")
        if type1 != "PERSON" and type2 != "PERSON":
            continue
            
        # Calculation weights
        call_contrib = sum(c["confidence"] * c["reliability"] * 2.0 for c in details["calls"])
        msg_contrib = sum(m["confidence"] * m["reliability"] * 1.5 for m in details["messages"])
        tx_contrib = sum(t["confidence"] * t["reliability"] * 10.0 for t in details["transfers"])
        device_contrib = sum(d["confidence"] * d["reliability"] * 20.0 for d in details["shared_devices"])
        
        # Calculate raw relationship score
        raw_score = call_contrib + msg_contrib + tx_contrib + device_contrib
        
        if raw_score == 0:
            continue
            
        normalized_score = min(100.0, (raw_score / RELATIONSHIP_SATURATION_CAP) * 100.0)
        normalized_score = float(round(normalized_score, 1))
        
        # Assemble supporting evidence
        evidence_list = []
        if details["calls"]:
            evidence_list.append(f"{len(details['calls'])} phone call(s)")
        if details["messages"]:
            evidence_list.append(f"{len(details['messages'])} message/email exchange(s)")
        if details["transfers"]:
            tot_amt = sum(t["amount"] for t in details["transfers"])
            evidence_list.append(f"{len(details['transfers'])} money transfer(s) totaling Rs.{tot_amt:,}")
        if details["shared_devices"]:
            resources_str = ", ".join(d["resource_name"] for d in details["shared_devices"])
            evidence_list.append(f"Shared connectivity to: {resources_str}")
            
        # Average relationship confidence
        all_confs = [c["confidence"] for c in details["calls"]] + \
                    [m["confidence"] for m in details["messages"]] + \
                    [t["confidence"] for t in details["transfers"]] + \
                    [d["confidence"] for d in details["shared_devices"]]
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 1.0
        
        relationship_profiles.append({
            "entity_1_id": ent1,
            "entity_1": name1,
            "entity_2_id": ent2,
            "entity_2": name2,
            "risk_score": normalized_score,
            "risk_level": assign_risk_level(normalized_score),
            "interaction_counts": {
                "calls": len(details["calls"]),
                "messages": len(details["messages"]),
                "transfers": len(details["transfers"]),
                "shared_devices": len(details["shared_devices"])
            },
            "supporting_evidence": evidence_list,
            "confidence": float(round(avg_conf, 2))
        })
        
    # Sort relationship profiles by risk score descending
    relationship_profiles.sort(key=lambda x: x["risk_score"], reverse=True)
    return relationship_profiles
