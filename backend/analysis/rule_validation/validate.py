"""
Rule-Based Validation Layer
============================
Scans unified_graph.json for concrete, deterministic violations.
No ML, no guesswork — pure pattern matching against predefined forensic rules.

Rules Implemented:
  1. SMURFING_DETECTED    — rapid sub-threshold transfers from one source
  2. FORENSIC_HIT         — explicit forensic signal flags in communications
  3. COMMUNICATION_BURST  — unusually dense comms between actors in a time window
  4. RENDEZVOUS           — multiple persons co-located within ±15 minutes
  5. CO_CORROBORATION     — entity appears across 3+ distinct data sources

Run standalone:
    cd backend
    python -m rule_validation.validate
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Neo4j integration (optional — falls back to JSON if unavailable)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from db_helper.dp_helper import get_graph_data_from_neo4j, is_neo4j_available
    _NEO4J_IMPORTED = True
except ImportError:
    _NEO4J_IMPORTED = False

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GRAPH_PATH = Path(__file__).parent.parent.parent / "Graph_Integration_Layer" / "output" / "unified_graph.json"
OUTPUT_PATH = Path(__file__).parent / "flags.json"

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S+05:30",
]

# Rule thresholds — easy to tune
SMURF_AMOUNT_THRESHOLD = 10000       # max per-transfer amount (INR)
SMURF_MIN_TRANSFERS = 3              # minimum transfers from one source
SMURF_WINDOW_MINUTES = 30            # time window for rapid transfers

BURST_MIN_INTERACTIONS = 5           # minimum interactions to flag
BURST_WINDOW_MINUTES = 60            # sliding window size

COLOCATION_TIME_TOLERANCE_MIN = 15   # ±15 minutes overlap
CORROBORATION_MIN_SOURCES = 3        # minimum distinct data sources


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
            print("[rule_validation] Using Neo4j as data source.")
            return get_graph_data_from_neo4j()
        except Exception as e:
            print(f"[rule_validation] Neo4j failed ({e}), falling back to JSON.")
    print("[rule_validation] Using unified_graph.json (fallback).")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Helpers
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
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def normalize_ts(dt: datetime) -> datetime:
    """Strip timezone info for safe comparison."""
    if dt and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


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


def build_lookups(graph: dict) -> tuple[dict, dict]:
    """
    Build lookup dictionaries from the graph.
    Returns:
        masters: { master_id: master_entity_dict }
        name_map: { master_id: "human readable name" }
    """
    masters = {}
    name_map = {}
    for m in graph.get("master_entities", []):
        mid = m["master_id"]
        masters[mid] = m
        name_map[mid] = get_entity_name(m)
    return masters, name_map


def severity_for_amount(total: float) -> str:
    """Assign severity based on total transaction volume."""
    if total >= 50000:
        return "CRITICAL"
    if total >= 25000:
        return "HIGH"
    return "MEDIUM"


# ---------------------------------------------------------------------------
# Rule 1: Smurfing Detection
# ---------------------------------------------------------------------------
def detect_smurfing(relations: list, name_map: dict) -> list[dict]:
    """
    Detect structuring / smurfing patterns:
    A single source sends multiple transfers in a short window,
    each under the reporting threshold, to avoid AML detection.
    """
    # Filter TRANSFERRED_TO relations
    transfers = [
        r for r in relations
        if r.get("relation") == "TRANSFERRED_TO"
    ]

    # Group by source account
    by_source = defaultdict(list)
    for t in transfers:
        by_source[t["source"]].append(t)

    flags = []
    for source_id, txns in by_source.items():
        if len(txns) < SMURF_MIN_TRANSFERS:
            continue

        # Parse and sort by timestamp
        timed = []
        for t in txns:
            ts = parse_timestamp(t.get("timestamp", ""))
            if ts:
                timed.append((normalize_ts(ts), t))
        timed.sort(key=lambda x: x[0])

        if len(timed) < SMURF_MIN_TRANSFERS:
            continue

        # Sliding window: find clusters of rapid transfers
        for i in range(len(timed)):
            window_end = timed[i][0] + timedelta(minutes=SMURF_WINDOW_MINUTES)
            cluster = [(ts, t) for ts, t in timed[i:] if ts <= window_end]

            if len(cluster) < SMURF_MIN_TRANSFERS:
                continue

            amounts = [
                t.get("attributes", {}).get("amount", 0)
                for _, t in cluster
            ]

            # Check if ALL transfers are under the threshold
            if not all(a < SMURF_AMOUNT_THRESHOLD for a in amounts):
                continue

            total = sum(amounts)
            recipients = [
                name_map.get(t["target"], t["target"])
                for _, t in cluster
            ]
            recipient_ids = [t["target"] for _, t in cluster]

            first_ts = cluster[0][0]
            last_ts = cluster[-1][0]
            window_str = f"{first_ts.strftime('%H:%M')} - {last_ts.strftime('%H:%M')}"
            duration_min = int((last_ts - first_ts).total_seconds() / 60)

            flags.append({
                "rule": "SMURFING_DETECTED",
                "severity": severity_for_amount(total),
                "account_id": source_id,
                "account_name": name_map.get(source_id, source_id),
                "recipients": recipients,
                "recipient_ids": recipient_ids,
                "amounts": amounts,
                "total_amount": total,
                "transfer_count": len(cluster),
                "time_window": window_str,
                "duration_minutes": duration_min,
                "description": (
                    f"{len(cluster)} rapid transfers under Rs.{SMURF_AMOUNT_THRESHOLD:,} each "
                    f"within {duration_min} minutes -- total Rs.{total:,}"
                ),
            })
            break  # One flag per source is enough

    return flags


# ---------------------------------------------------------------------------
# Rule 2: Forensic Signal Hits
# ---------------------------------------------------------------------------
def detect_forensic_hits(relations: list, name_map: dict) -> list[dict]:
    """
    Scan all relations for explicit forensic signal flags.
    Checks both email-style signals (delete_instruction, impersonates_bank, etc.)
    and chat-style signals (has_urgency, has_money_ref, has_coordination, etc.)
    """
    SIGNAL_NAMES = {
        # Email signals
        "delete_instruction", "urgency_language", "impersonates_bank",
        "requests_otp", "requests_account_info",
        # Chat signals
        "has_urgency", "has_money_ref", "has_target_ref", "has_coordination",
    }

    flags = []
    for rel in relations:
        attrs = rel.get("attributes", {})
        forensic = attrs.get("forensic_signals", {})
        if not forensic:
            continue

        # Check each known signal
        for signal_name in SIGNAL_NAMES:
            if forensic.get(signal_name) is True:
                channel = rel.get("relation", "unknown").lower()
                if channel == "messaged":
                    channel = "chat"
                elif channel == "emailed":
                    channel = "email"

                flags.append({
                    "rule": "FORENSIC_HIT",
                    "severity": "HIGH" if signal_name in ("delete_instruction", "impersonates_bank", "has_urgency") else "MEDIUM",
                    "channel": channel,
                    "source": name_map.get(rel["source"], rel["source"]),
                    "source_id": rel["source"],
                    "target": name_map.get(rel["target"], rel["target"]),
                    "target_id": rel["target"],
                    "signal": signal_name,
                    "timestamp": rel.get("timestamp", ""),
                    "text_snippet": (attrs.get("text", "") or attrs.get("subject", ""))[:120],
                    "description": (
                        f"{channel.upper()} from {name_map.get(rel['source'], '?')} "
                        f"-> {name_map.get(rel['target'], '?')} flagged: {signal_name}"
                    ),
                })

    return flags


# ---------------------------------------------------------------------------
# Rule 3: Communication Burst
# ---------------------------------------------------------------------------
def detect_communication_burst(relations: list, name_map: dict) -> list[dict]:
    """
    Flag pairs of actors who exchange an unusually high number of
    calls/messages/emails within a sliding 60-minute window.
    """
    COMM_TYPES = {"CALLED", "MESSAGED", "EMAILED"}

    comms = [r for r in relations if r.get("relation") in COMM_TYPES]

    # Group by actor-pair (merge both directions into a canonical pair)
    by_pair = defaultdict(list)
    for r in comms:
        a, b = sorted([r["source"], r["target"]])
        ts = parse_timestamp(r.get("timestamp", ""))
        if ts:
            by_pair[(a, b)].append(normalize_ts(ts))

    flags = []
    for (a, b), timestamps in by_pair.items():
        timestamps.sort()
        if len(timestamps) < BURST_MIN_INTERACTIONS:
            continue

        # Sliding window
        for i in range(len(timestamps)):
            window_end = timestamps[i] + timedelta(minutes=BURST_WINDOW_MINUTES)
            in_window = [t for t in timestamps[i:] if t <= window_end]

            if len(in_window) >= BURST_MIN_INTERACTIONS:
                window_str = (
                    f"{timestamps[i].strftime('%H:%M')} - "
                    f"{in_window[-1].strftime('%H:%M')}"
                )
                flags.append({
                    "rule": "COMMUNICATION_BURST",
                    "severity": "HIGH" if len(in_window) >= 8 else "MEDIUM",
                    "actors": [
                        name_map.get(a, a),
                        name_map.get(b, b),
                    ],
                    "actor_ids": [a, b],
                    "count": len(in_window),
                    "window": window_str,
                    "description": (
                        f"{len(in_window)} interactions between "
                        f"{name_map.get(a, '?')} and {name_map.get(b, '?')} "
                        f"in {BURST_WINDOW_MINUTES}-min window ({window_str})"
                    ),
                })
                break  # One flag per pair

    return flags


# ---------------------------------------------------------------------------
# Rule 4: Co-Location / Rendezvous Detection
# ---------------------------------------------------------------------------
def detect_colocation(
    relations: list, masters: dict, name_map: dict
) -> list[dict]:
    """
    Detect co-location events: 2+ PERSON (or ENTITY) entities observed
    at the same location within ±15 minutes of each other.
    """
    # Collect LOCATED_AT relations, grouped by target location
    location_visits = defaultdict(list)  # location_id → [(person_id, datetime)]

    for rel in relations:
        if rel.get("relation") != "LOCATED_AT":
            continue

        person_id = rel["source"]
        location_id = rel["target"]
        ts = parse_timestamp(rel.get("timestamp", ""))

        if not ts:
            continue

        # Only consider PERSON or mobile entity types (vehicles, devices)
        person_master = masters.get(person_id, {})
        ptype = person_master.get("master_type", "")
        if ptype not in ("PERSON", "ENTITY"):
            continue

        location_visits[location_id].append((person_id, normalize_ts(ts)))

    flags = []
    for location_id, visits in location_visits.items():
        # Need at least 2 different entities
        unique_entities = set(v[0] for v in visits)
        if len(unique_entities) < 2:
            continue

        # Check all pairs for time overlap
        visits.sort(key=lambda x: x[1])
        overlapping_groups = []

        for i, (pid_a, ts_a) in enumerate(visits):
            group = {pid_a: ts_a}
            for j in range(i + 1, len(visits)):
                pid_b, ts_b = visits[j]
                if pid_b == pid_a:
                    continue
                if abs((ts_b - ts_a).total_seconds()) <= COLOCATION_TIME_TOLERANCE_MIN * 60:
                    group[pid_b] = ts_b

            if len(group) >= 2:
                # Check if we already have a superset group
                group_key = frozenset(group.keys())
                if not any(group_key <= existing for existing in overlapping_groups):
                    overlapping_groups.append(group_key)

                    persons = [name_map.get(pid, pid) for pid in group.keys()]
                    person_ids = list(group.keys())
                    timestamps_str = [
                        ts.strftime("%H:%M") for ts in group.values()
                    ]

                    flags.append({
                        "rule": "RENDEZVOUS",
                        "severity": "HIGH" if len(group) >= 3 else "MEDIUM",
                        "persons": persons,
                        "person_ids": person_ids,
                        "location": name_map.get(location_id, location_id),
                        "location_id": location_id,
                        "timestamps": timestamps_str,
                        "description": (
                            f"{', '.join(persons)} co-located at "
                            f"{name_map.get(location_id, '?')} "
                            f"(within ±{COLOCATION_TIME_TOLERANCE_MIN} min)"
                        ),
                    })

    # Deduplicate: keep only unique person-set + location combos
    seen = set()
    unique_flags = []
    for f in flags:
        key = (frozenset(f["person_ids"]), f["location_id"])
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    return unique_flags


# ---------------------------------------------------------------------------
# Rule 5: Cross-Source Corroboration
# ---------------------------------------------------------------------------
def detect_cross_source_corroboration(
    relations: list, masters: dict, name_map: dict
) -> list[dict]:
    """
    Flag entities that appear across 3+ distinct raw data source types.
    This indicates strong multi-source evidence corroboration.
    """
    entity_sources = defaultdict(set)

    for rel in relations:
        # Determine source_type (some older relations use 'provenance' instead)
        st = rel.get("source_type", "")
        if not st:
            prov = rel.get("provenance", "")
            if prov:
                st = prov.split(":")[0].replace(".txt", "").replace(".json", "")

        if not st:
            continue

        for eid in [rel.get("source"), rel.get("target")]:
            if eid:
                entity_sources[eid].add(st)

    flags = []
    for entity_id, sources in entity_sources.items():
        if len(sources) < CORROBORATION_MIN_SOURCES:
            continue

        master = masters.get(entity_id, {})
        flags.append({
            "rule": "CO_CORROBORATION",
            "severity": "HIGH" if len(sources) >= 5 else "MEDIUM",
            "entity_name": name_map.get(entity_id, entity_id),
            "entity_id": entity_id,
            "entity_type": master.get("master_type", "UNKNOWN"),
            "sources": sorted(sources),
            "source_count": len(sources),
            "description": (
                f"{name_map.get(entity_id, '?')} appears across "
                f"{len(sources)} data sources: {', '.join(sorted(sources))}"
            ),
        })

    # Sort by source count descending
    flags.sort(key=lambda f: f["source_count"], reverse=True)
    return flags


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run_all_rules() -> dict:
    """
    Execute all validation rules against the unified graph.
    Returns the complete flags report and saves to flags.json.
    """
    print(f"Loading graph from: {GRAPH_PATH}")
    graph = load_graph()

    masters, name_map = build_lookups(graph)
    relations = graph.get("relations", [])

    print(f"  Entities: {len(masters)}, Relations: {len(relations)}")
    print("  Running rule-based validation...\n")

    # Execute each rule
    print("  [1/5] Detecting smurfing patterns...")
    smurfing = detect_smurfing(relations, name_map)
    print(f"         -> {len(smurfing)} flag(s)")

    print("  [2/5] Scanning for forensic signal hits...")
    forensic_hits = detect_forensic_hits(relations, name_map)
    print(f"         -> {len(forensic_hits)} flag(s)")

    print("  [3/5] Detecting communication bursts...")
    comm_bursts = detect_communication_burst(relations, name_map)
    print(f"         -> {len(comm_bursts)} flag(s)")

    print("  [4/5] Detecting co-location / rendezvous events...")
    colocations = detect_colocation(relations, masters, name_map)
    print(f"         -> {len(colocations)} flag(s)")

    print("  [5/5] Checking cross-source corroboration...")
    corroboration = detect_cross_source_corroboration(relations, masters, name_map)
    print(f"         -> {len(corroboration)} flag(s)")

    # Assemble output
    all_flags = {
        "smurfing": smurfing,
        "forensic_hits": forensic_hits,
        "communication_bursts": comm_bursts,
        "colocations": colocations,
        "cross_source_corroboration": corroboration,
    }
    total = sum(len(v) for v in all_flags.values())

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_flags": total,
        "severity_summary": {
            "CRITICAL": sum(
                1 for cat in all_flags.values()
                for f in cat if f.get("severity") == "CRITICAL"
            ),
            "HIGH": sum(
                1 for cat in all_flags.values()
                for f in cat if f.get("severity") == "HIGH"
            ),
            "MEDIUM": sum(
                1 for cat in all_flags.values()
                for f in cat if f.get("severity") == "MEDIUM"
            ),
        },
        "flags": all_flags,
    }

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*60}")
    print(f"[OK] Validation complete -- {total} flags saved to: {OUTPUT_PATH}")
    print(f"     CRITICAL: {report['severity_summary']['CRITICAL']}")
    print(f"     HIGH:     {report['severity_summary']['HIGH']}")
    print(f"     MEDIUM:   {report['severity_summary']['MEDIUM']}")
    print(f"{'='*60}")

    return report


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_all_rules()
