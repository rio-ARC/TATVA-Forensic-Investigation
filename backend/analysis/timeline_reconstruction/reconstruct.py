"""
Timeline Reconstruction Layer
===============================
Reads unified_graph.json → extracts every timestamped event → sorts
chronologically → groups into 30-minute "scene" windows → writes timeline.json

Each scene captures:
  - What happened (calls, transfers, messages, movements)
  - Who was involved
  - Which data sources contributed
  - Human-readable event descriptions

Run standalone:
    cd backend
    python -m timeline_reconstruction.reconstruct
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

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
OUTPUT_PATH = Path(__file__).parent / "timeline.json"

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S+05:30",
]

SCENE_WINDOW_MINUTES = 30  # group events into 30-minute windows


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
            print("[timeline_reconstruction] Using Neo4j as data source.")
            return get_graph_data_from_neo4j()
        except Exception as e:
            print(f"[timeline_reconstruction] Neo4j failed ({e}), falling back to JSON.")
    print("[timeline_reconstruction] Using unified_graph.json (fallback).")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Name Resolution
# ---------------------------------------------------------------------------
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

    if master_type == "PLACE":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.title()

    if master_type == "INFRASTRUCTURE":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.title()

    if master_type == "ENTITY":
        for val in resolved:
            if val and "\n" not in val and len(val) < 80:
                return val.upper() if val.startswith("acc") else val.title()

    for val in resolved:
        if val and "\n" not in val and len(val) < 80:
            return val.title()

    return master.get("master_id", "Unknown")


def build_name_map(masters: list) -> dict:
    """Build a mapping of master_id → human-readable name."""
    return {m["master_id"]: get_entity_name(m) for m in masters}


# ---------------------------------------------------------------------------
# Timestamp Parsing
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


# ---------------------------------------------------------------------------
# Event Description Formatting
# ---------------------------------------------------------------------------
def format_event_description(event: dict) -> str:
    """
    Create a human-readable single-line description for each event type.
    """
    action = event.get("action", "")
    from_name = event.get("from", "?")
    to_name = event.get("to", "?")
    attrs = event.get("attributes", {})

    if action == "CALLED":
        duration = attrs.get("duration", "?")
        call_type = attrs.get("call_type", "").lower()
        return f"{from_name} called {to_name} ({duration}s, {call_type})"

    if action == "EMAILED":
        subject = attrs.get("subject", "")
        signals = attrs.get("forensic_signals", {})
        active = [k for k, v in signals.items() if v is True]
        desc = f"{from_name} emailed {to_name}"
        if subject:
            desc += f" -- Subject: {subject}"
        if active:
            desc += f" [FLAGGED: {', '.join(active)}]"
        return desc

    if action == "MESSAGED":
        text = attrs.get("text", "")
        snippet = text[:80] + ("..." if len(text) > 80 else "")
        return f"{from_name} -> {to_name}: '{snippet}'"

    if action == "TRANSFERRED_TO":
        amount = attrs.get("amount", "?")
        method = attrs.get("transaction_type", "?")
        return f"{from_name} -> {to_name}: Rs.{amount:,} ({method})"

    if action == "LOCATED_AT":
        accuracy = attrs.get("accuracy", "?")
        speed = attrs.get("speed", 0)
        motion = "moving" if speed and speed > 1 else "stationary"
        return f"{from_name} at {to_name} (accuracy: {accuracy}m, {motion})"

    if action == "CONNECTED_TO_TOWER":
        return f"{from_name} connected to {to_name}"

    if action == "MOVED_TO":
        distance = attrs.get("distance_meters", "?")
        if isinstance(distance, (int, float)):
            distance = f"{distance:.0f}"
        return f"Movement: {from_name} -> {to_name} ({distance}m)"

    if action == "DETECTED":
        return f"Camera detected: {to_name} at {from_name}"

    if action in ("POSTED_ON", "MENTIONED_USER"):
        content = attrs.get("content", "")
        snippet = content[:80] + ("..." if len(content) > 80 else "")
        return f"{from_name} posted on {to_name}: '{snippet}'" if content else f"{from_name} -> {to_name}"

    if action == "MENTIONED":
        return f"{from_name} mentioned {to_name}"

    if action == "TRANSFERRED_MONEY":
        return f"{from_name} transferred money to {to_name} (FIR reference)"

    # Fallback
    return f"{action}: {from_name} -> {to_name}"


# ---------------------------------------------------------------------------
# Event List Builder
# ---------------------------------------------------------------------------
def build_event_list(relations: list, name_map: dict) -> list[dict]:
    """
    Convert each relation into a structured event dict.
    Only includes relations with parseable timestamps.
    Returns events sorted chronologically.
    """
    events = []

    for rel in relations:
        ts_raw = rel.get("timestamp", "")
        ts = parse_timestamp(ts_raw)
        if not ts:
            continue

        ts_normalized = normalize_ts(ts)

        # Determine source type (handle both source_type and provenance fields)
        source_type = rel.get("source_type", "")
        if not source_type:
            prov = rel.get("provenance", "")
            if prov:
                source_type = prov.split(":")[0].replace(".txt", "").replace(".json", "")

        event = {
            "timestamp": ts_normalized.isoformat(),
            "parsed_time": ts_normalized,  # kept for sorting, removed before output
            "action": rel.get("relation", "UNKNOWN"),
            "from": name_map.get(rel.get("source", ""), rel.get("source", "?")),
            "from_id": rel.get("source", ""),
            "to": name_map.get(rel.get("target", ""), rel.get("target", "?")),
            "to_id": rel.get("target", ""),
            "source_type": source_type or "unknown",
            "confidence": rel.get("confidence", 0.0),
            "attributes": rel.get("attributes", {}),
        }

        # Generate human-readable description
        event["description"] = format_event_description(event)

        events.append(event)

    # Sort by timestamp
    events.sort(key=lambda e: e["parsed_time"])
    return events


# ---------------------------------------------------------------------------
# Scene Grouping
# ---------------------------------------------------------------------------
def assign_scene_label(events: list[dict]) -> str:
    """
    Auto-generate a descriptive label for a scene based on the dominant
    event types within it.
    """
    action_counts = Counter(e["action"] for e in events)
    top_actions = action_counts.most_common(3)
    top_names = [a for a, _ in top_actions]

    # Map action combos to readable labels
    if "TRANSFERRED_TO" in top_names:
        return "Financial Transfers"
    if "CALLED" in top_names and "MESSAGED" in top_names:
        return "Coordinated Communications"
    if "CALLED" in top_names:
        return "Voice Communications"
    if "MESSAGED" in top_names:
        return "Chat Activity"
    if "EMAILED" in top_names:
        return "Email Exchange"
    if "LOCATED_AT" in top_names and "MOVED_TO" in top_names:
        return "Movement & Tracking"
    if "LOCATED_AT" in top_names:
        return "Location Tracking"
    if "DETECTED" in top_names:
        return "Surveillance Detection"
    if "POSTED_ON" in top_names:
        return "Social Media Activity"
    if "MENTIONED" in top_names:
        return "Entity Mentions"
    if "CONNECTED_TO_TOWER" in top_names:
        return "Cell Tower Connections"

    return "Mixed Activity"


def group_into_scenes(
    events: list[dict],
    window_minutes: int = SCENE_WINDOW_MINUTES,
) -> list[dict]:
    """
    Group chronological events into time-windowed "scenes".
    Each scene is a 30-minute bucket from the earliest event.
    """
    if not events:
        return []

    earliest = events[0]["parsed_time"]
    latest = events[-1]["parsed_time"]

    # Create time buckets
    buckets = defaultdict(list)
    for event in events:
        offset = (event["parsed_time"] - earliest).total_seconds() / 60
        bucket_idx = int(offset // window_minutes)
        buckets[bucket_idx].append(event)

    scenes = []
    for idx in sorted(buckets.keys()):
        bucket_events = buckets[idx]
        window_start = earliest + timedelta(minutes=idx * window_minutes)
        window_end = window_start + timedelta(minutes=window_minutes)

        # Collect source types for this scene
        source_types = Counter(e["source_type"] for e in bucket_events)
        dominant_sources = [s for s, _ in source_types.most_common(3)]

        # Collect action types
        action_types = Counter(e["action"] for e in bucket_events)

        # Collect unique actors in this scene
        actors = set()
        for e in bucket_events:
            actors.add(e["from"])
            actors.add(e["to"])

        # Clean events for output (remove internal parsed_time)
        clean_events = []
        for e in bucket_events:
            clean_e = {k: v for k, v in e.items() if k != "parsed_time"}
            clean_events.append(clean_e)

        scene_label = assign_scene_label(bucket_events)

        scene = {
            "scene_id": f"SCENE_{idx + 1:02d}",
            "window_start": window_start.strftime("%H:%M"),
            "window_end": window_end.strftime("%H:%M"),
            "label": scene_label,
            "event_count": len(bucket_events),
            "action_breakdown": dict(action_types.most_common()),
            "dominant_source_types": dominant_sources,
            "active_actors": sorted(actors - {"?", "Unknown"}),
            "events": clean_events,
        }
        scenes.append(scene)

    return scenes


# ---------------------------------------------------------------------------
# Summary Stats
# ---------------------------------------------------------------------------
def compute_timeline_stats(events: list[dict], scenes: list[dict]) -> dict:
    """Compute high-level statistics about the timeline."""
    if not events:
        return {}

    action_counts = Counter(e["action"] for e in events)
    source_counts = Counter(e["source_type"] for e in events)

    # Find peak activity scene
    peak_scene = max(scenes, key=lambda s: s["event_count"]) if scenes else None

    return {
        "total_events": len(events),
        "total_scenes": len(scenes),
        "action_type_counts": dict(action_counts.most_common()),
        "source_type_counts": dict(source_counts.most_common()),
        "peak_activity_scene": peak_scene["scene_id"] if peak_scene else None,
        "peak_activity_count": peak_scene["event_count"] if peak_scene else 0,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run_reconstruction() -> dict:
    """
    Run the full timeline reconstruction pipeline and save to timeline.json.
    """
    print(f"Loading graph from: {GRAPH_PATH}")
    graph = load_graph()

    masters = graph.get("master_entities", [])
    relations = graph.get("relations", [])

    print(f"  Entities: {len(masters)}, Relations: {len(relations)}")

    # Build name map
    name_map = build_name_map(masters)

    # Build sorted event list
    print("  Building event list...")
    events = build_event_list(relations, name_map)
    print(f"  -> {len(events)} events with valid timestamps")

    # Determine incident window
    if events:
        first_ts = events[0]["parsed_time"]
        last_ts = events[-1]["parsed_time"]
        duration = (last_ts - first_ts).total_seconds() / 60
        incident_window = {
            "start": first_ts.isoformat(),
            "end": last_ts.isoformat(),
            "duration_minutes": round(duration, 1),
        }
        print(f"  Incident window: {first_ts.strftime('%H:%M')} -> {last_ts.strftime('%H:%M')} ({duration:.0f} min)")
    else:
        incident_window = {"start": None, "end": None, "duration_minutes": 0}

    # Group into scenes
    print(f"  Grouping into {SCENE_WINDOW_MINUTES}-minute scenes...")
    scenes = group_into_scenes(events, SCENE_WINDOW_MINUTES)
    print(f"  -> {len(scenes)} scenes generated")

    # Print scene overview
    for scene in scenes:
        print(f"     {scene['scene_id']}: {scene['window_start']}-{scene['window_end']} "
              f"| {scene['event_count']} events | {scene['label']}")

    # Compute stats
    stats = compute_timeline_stats(events, scenes)

    # Clean events for final output (remove parsed_time from top-level too)
    # (already cleaned inside group_into_scenes for scene events)

    # Assemble output
    timeline = {
        "generated_at": datetime.now().isoformat(),
        "incident_window": incident_window,
        "stats": stats,
        "total_events": len(events),
        "total_scenes": len(scenes),
        "scenes": scenes,
    }

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*60}")
    print(f"[OK] Timeline saved to: {OUTPUT_PATH}")
    print(f"     Events: {len(events)} across {len(scenes)} scenes")
    if stats.get("peak_activity_scene"):
        print(f"     Peak scene: {stats['peak_activity_scene']} ({stats['peak_activity_count']} events)")
    print(f"{'='*60}")

    return timeline


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_reconstruction()
