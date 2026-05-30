# TATVA Insights — Coding Plan

## Goal
Build 3 clean, independent analysis layers. Each reads `unified_graph.json` → runs logic → writes a structured JSON output.

---

## Current State (What Already Exists)

| Component | Location | Status |
|---|---|---|
| Unified graph pipeline | `Graph_Integration_Layer/` | ✅ Complete |
| **Output graph** | `Graph_Integration_Layer/output/unified_graph.json` | ✅ 77 KB, ~44 entities, ~120 relations |
| Monolithic insights | `insights/graph_insights.py` | ⚠️ Exists but mixes ALL logic (centrality + alerts + timeline) in one 400-line file |
| FastAPI server | `api/main.py` | ✅ Working, serves from `insights/` |
| Frontend | `frontend/` | ✅ Vite+React scaffold exists |

---

## New Structure

We will create **3 separate folders** inside `backend/`. Each folder has one main Python file and outputs one JSON.

```
backend/
├── Graph_Integration_Layer/
│   └── output/
│       └── unified_graph.json       ← INPUT (read-only)
│
├── rule_validation/                  ← NEW FOLDER
│   ├── __init__.py
│   └── validate.py                   → outputs rule_validation/flags.json
│
├── graph_summary/                    ← NEW FOLDER
│   ├── __init__.py
│   └── summarize.py                  → outputs graph_summary/summary.json
│
├── timeline_reconstruction/          ← NEW FOLDER
│   ├── __init__.py
│   └── reconstruct.py                → outputs timeline_reconstruction/timeline.json
│
├── insights/                         ← EXISTING (keep for API glue later)
├── api/                              ← EXISTING (will import from new folders later)
└── requirements.txt
```

> [!IMPORTANT]
> Each module is **self-contained**. You can run any one of them independently:
> ```bash
> cd backend
> python -m rule_validation.validate
> python -m graph_summary.summarize
> python -m timeline_reconstruction.reconstruct
> ```

---

## Shared Helper: Loading the Graph

Every module needs to load and parse the same `unified_graph.json`. Rather than duplicating code, each file has its own simple `load_graph()` function (since we want zero cross-folder dependencies and simplicity):

```python
import json
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "Graph_Integration_Layer" / "output" / "unified_graph.json"

def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
```

---

## Layer 1: Rule-Based Validation (`rule_validation/validate.py`)

### Purpose
Scan the graph for **concrete, deterministic violations** — no guesswork, no ML. Pure pattern matching.

### Functions to Write

```python
def load_graph() -> dict
    # Load unified_graph.json, return {"master_entities": [...], "relations": [...]}

def build_lookups(graph: dict) -> tuple[dict, dict]
    # Returns:
    #   masters: { master_id: master_entity_dict }
    #   name_map: { master_id: "human readable name" }

def detect_smurfing(relations: list, name_map: dict) -> list[dict]
    # Logic:
    #   1. Filter relations where relation == "TRANSFERRED_TO"
    #   2. Group by source account
    #   3. For each source with >= 3 transfers:
    #      - Sort by timestamp
    #      - Check if all happened within a 30-minute window
    #      - Check if each amount < 10000
    #   4. Return flag with: account, recipients, amounts, total, time_window

def detect_forensic_hits(relations: list, name_map: dict) -> list[dict]
    # Logic:
    #   1. For each relation, check attributes.forensic_signals
    #   2. If any signal (delete_instruction, urgency_language, 
    #      impersonates_bank, has_coordination, has_money_ref) is True
    #   3. Return flag with: channel (email/chat), source, target, signal_name, timestamp

def detect_communication_burst(relations: list, name_map: dict) -> list[dict]
    # Logic:
    #   1. Filter relations where relation in ["CALLED", "MESSAGED", "EMAILED"]
    #   2. Group by (source, target) pair (merge both directions)
    #   3. Sort each group by timestamp
    #   4. Sliding 60-minute window: if count >= 5 interactions → flag
    #   5. Return: actors, count, window_start, window_end

def detect_colocation(relations: list, masters: dict, name_map: dict) -> list[dict]
    # Logic:
    #   1. Filter relations where relation == "LOCATED_AT"
    #   2. Group by target (location master_id)
    #   3. For each location group: check if 2+ different PERSON entities 
    #      have timestamps within ±15 minutes
    #   4. Return: persons, location_name, overlapping_timestamps

def detect_cross_source_corroboration(relations: list, masters: dict, name_map: dict) -> list[dict]
    # Logic:
    #   1. For each master entity, collect all source_type values from 
    #      relations where it appears as source or target
    #   2. If unique source_types count >= 3 → flag
    #   3. Return: entity_name, master_id, sources list, count

def run_all_rules() -> dict
    # Orchestrator: calls all detect_* functions, assembles final output dict
    # Saves to rule_validation/flags.json
```

### Output Schema (`rule_validation/flags.json`)

```json
{
  "generated_at": "2026-05-30T13:00:00",
  "total_flags": 12,
  "flags": {
    "smurfing": [
      {
        "rule": "SMURFING_DETECTED",
        "severity": "CRITICAL",
        "account_id": "MASTER_b41353c7",
        "account_name": "Rahul Sen (acc1001)",
        "recipients": ["acc2001", "acc3001", "acc4001", "acc6001", "acc7001"],
        "amounts": [5000, 7000, 4500, 4900, 5100],
        "total_amount": 26500,
        "time_window": "22:11 - 22:30",
        "description": "5 rapid UPI transfers under ₹10k each within 19 minutes"
      }
    ],
    "forensic_hits": [
      {
        "rule": "FORENSIC_HIT",
        "severity": "HIGH",
        "channel": "email",
        "source": "Rahul Sen",
        "target": "Arjun Ghosh",
        "signal": "delete_instruction",
        "timestamp": "2026-05-22T20:30:00+05:30",
        "description": "Email contains delete_instruction flag"
      }
    ],
    "communication_bursts": [],
    "colocations": [],
    "cross_source_corroboration": []
  }
}
```

---

## Layer 2: Graph Summary & Centrality (`graph_summary/summarize.py`)

### Purpose
Extract graph-level stats and compute per-entity importance scores using NetworkX.

### Functions to Write

```python
def load_graph() -> dict

def build_networkx_graph(graph: dict) -> nx.DiGraph
    # Add all master entities as nodes
    # Add all relations as edges with type and confidence as attributes
    # Return DiGraph

def compute_entity_counts(masters: dict) -> dict
    # Count entities by master_type: {"PERSON": 5, "PLACE": 12, ...}

def compute_relation_counts(relations: list) -> dict
    # Count relations by type: {"CALLED": 20, "TRANSFERRED_TO": 7, ...}

def compute_centrality(G: nx.DiGraph) -> dict
    # Returns per-node: {
    #   master_id: {
    #     "degree": 0.45,
    #     "betweenness": 0.31,
    #     "in_degree": 0.2,
    #     "out_degree": 0.25
    #   }
    # }

def build_entity_profiles(masters: dict, relations: list, centrality: dict) -> list[dict]
    # For each master entity, build a profile:
    #   - master_id, name, master_type
    #   - entity_types (from source data)
    #   - resolved_values
    #   - degree_centrality, betweenness_centrality
    #   - source_types: unique set of source_type from all relations touching this entity
    #   - source_count: len(source_types)
    #   - relation_count: number of relations where entity is source or target

def compute_incident_window(relations: list) -> dict
    # Parse all timestamps, find min and max
    # Return: { "start": "2026-05-22T20:30:00", "end": "2026-05-22T23:00:00", "duration_minutes": 150 }

def run_summary() -> dict
    # Orchestrator: calls all functions, assembles output
    # Saves to graph_summary/summary.json
```

### Output Schema (`graph_summary/summary.json`)

```json
{
  "generated_at": "2026-05-30T13:00:00",
  "overview": {
    "total_entities": 44,
    "total_relations": 120,
    "entity_type_counts": { "PERSON": 8, "PLACE": 15, "INFRASTRUCTURE": 9, "ENTITY": 12 },
    "relation_type_counts": { "CALLED": 20, "TRANSFERRED_TO": 18, "LOCATED_AT": 15 },
    "incident_window": {
      "start": "2026-05-22T20:30:00",
      "end": "2026-05-22T23:00:00",
      "duration_minutes": 150
    },
    "data_sources_present": ["fir_document", "cdr_record", "mobile_gps", "bank_transaction", "vehicle_camera"]
  },
  "entity_profiles": [
    {
      "master_id": "MASTER_b41353c7",
      "name": "Rahul Sen",
      "master_type": "PERSON",
      "entity_types": ["PERSON", "PHONE_NUMBER", "ACCOUNT", "DEVICE"],
      "resolved_values": ["rahul sen", "9876543210", "acc1001", "android_001"],
      "degree_centrality": 0.45,
      "betweenness_centrality": 0.31,
      "in_degree_centrality": 0.20,
      "out_degree_centrality": 0.25,
      "source_types": ["fir_document", "cdr_record", "mobile_gps", "bank_transaction"],
      "source_count": 4,
      "relation_count": 38
    }
  ]
}
```

---

## Layer 3: Timeline Reconstruction (`timeline_reconstruction/reconstruct.py`)

### Purpose
Build a chronologically ordered event stream, then group into "scenes" by 30-minute windows.

### Functions to Write

```python
def load_graph() -> dict

def build_name_map(masters: dict) -> dict
    # master_id → best human-readable name (prefer person name > account > id)

def parse_timestamp(ts_str: str) -> datetime | None
    # Try multiple formats:
    #   "%Y-%m-%d %H:%M:%S"
    #   "%Y-%m-%dT%H:%M:%S"
    #   "%Y-%m-%dT%H:%M:%S%z"  (with timezone offset)
    #   "%Y-%m-%dT%H:%M:%S.%f" (with microseconds)
    # Return None if unparseable

def build_event_list(relations: list, name_map: dict) -> list[dict]
    # For each relation with a parseable timestamp:
    #   - Create event dict: timestamp, parsed_time, action, from_name, to_name, 
    #     source_type, confidence, attributes (subset of original)
    # Sort by parsed_time
    # Return sorted list

def format_event_description(event: dict) -> str
    # Human-readable single-line description:
    #   CALLED    → "Rahul Sen called Arjun Ghosh (320s, outgoing)"
    #   EMAILED   → "Rahul Sen emailed Arjun Ghosh — Subject: Tonight's transfer"
    #   MESSAGED  → "Arjun Ghosh → Group Chat: 'I am ready. Coordinate with Vikram...'"
    #   TRANSFERRED_TO → "acc1001 → acc2001: ₹5,000 (UPI)"
    #   LOCATED_AT → "Rahul Sen at Chatterjee Lane, Bowbazar (accuracy: 4.2m)"
    #   DETECTED   → "Camera detected vehicle at checkpoint"
    #   Fallback   → "RELATION_TYPE: Source → Target"

def group_into_scenes(events: list, window_minutes: int = 30) -> list[dict]
    # 1. Find earliest timestamp
    # 2. Create 30-min buckets from earliest to latest
    # 3. Assign each event to a bucket
    # 4. For each non-empty bucket, create a scene:
    #    {
    #      "scene_id": "SCENE_01",
    #      "window_start": "20:30",
    #      "window_end": "21:00",
    #      "event_count": 8,
    #      "dominant_source_types": ["cdr_record", "mobile_gps"],
    #      "events": [...]
    #    }

def run_reconstruction() -> dict
    # Orchestrator: load graph, build events, group into scenes
    # Saves to timeline_reconstruction/timeline.json
```

### Output Schema (`timeline_reconstruction/timeline.json`)

```json
{
  "generated_at": "2026-05-30T13:00:00",
  "incident_window": {
    "start": "2026-05-22T20:30:00",
    "end": "2026-05-22T23:00:00"
  },
  "total_events": 85,
  "total_scenes": 6,
  "scenes": [
    {
      "scene_id": "SCENE_01",
      "window_start": "20:30",
      "window_end": "21:00",
      "event_count": 12,
      "dominant_source_types": ["cdr_record", "email", "chat"],
      "events": [
        {
          "timestamp": "2026-05-22T20:30:00",
          "action": "CALLED",
          "from": "Rahul Sen",
          "to": "Arjun Ghosh",
          "description": "Rahul Sen called Arjun Ghosh (185s, outgoing)",
          "source_type": "cdr_record",
          "confidence": 0.99
        },
        {
          "timestamp": "2026-05-22T20:30:00",
          "action": "LOCATED_AT",
          "from": "Rahul Sen",
          "to": "Chatterjee Lane, Bowbazar, Kolkata",
          "description": "Rahul Sen at Chatterjee Lane, Bowbazar (accuracy: 4.2m, stationary)",
          "source_type": "mobile_gps",
          "confidence": 0.95
        }
      ]
    },
    {
      "scene_id": "SCENE_02",
      "window_start": "21:00",
      "window_end": "21:30",
      "event_count": 10,
      "dominant_source_types": ["cdr_record", "mobile_gps", "telecom_tower"],
      "events": []
    }
  ]
}
```

---

## Implementation Order

> [!TIP]
> Build in this exact order. Each step is testable independently.

### Step 1: `graph_summary/summarize.py` (~45 min)
**Why first:** It's the simplest. You learn the graph's shape (entity names, relation types, source types) which helps you write better rules and timeline formatting.

1. Create `backend/graph_summary/__init__.py` (empty)
2. Create `backend/graph_summary/summarize.py`
3. Implement `load_graph()`, `compute_entity_counts()`, `compute_relation_counts()`
4. Implement `build_networkx_graph()` and `compute_centrality()`
5. Implement `build_entity_profiles()` and `compute_incident_window()`
6. Implement `run_summary()` — save to `graph_summary/summary.json`
7. Test: `python -m graph_summary.summarize` → check JSON output

---

### Step 2: `rule_validation/validate.py` (~90 min)
**Why second:** Rules depend on understanding entity names and relation types, which Step 1 clarified.

1. Create `backend/rule_validation/__init__.py` (empty)
2. Create `backend/rule_validation/validate.py`
3. Implement `build_lookups()` (reuse name-mapping logic from Step 1)
4. Implement `detect_smurfing()` — the most critical rule
5. Implement `detect_forensic_hits()` — scan for signal flags in attributes
6. Implement `detect_communication_burst()` — sliding window over sorted comms
7. Implement `detect_colocation()` — same-location timestamp overlap
8. Implement `detect_cross_source_corroboration()` — count source types per entity
9. Implement `run_all_rules()` — save to `rule_validation/flags.json`
10. Test: `python -m rule_validation.validate` → verify flags match expected data

---

### Step 3: `timeline_reconstruction/reconstruct.py` (~60 min)
**Why third:** It's the most polished, user-facing output. By now you know all entity names and relation types.

1. Create `backend/timeline_reconstruction/__init__.py` (empty)
2. Create `backend/timeline_reconstruction/reconstruct.py`
3. Implement `parse_timestamp()` with multi-format support
4. Implement `build_event_list()` — extract, format, sort
5. Implement `format_event_description()` — per relation-type formatting
6. Implement `group_into_scenes()` — 30-min window bucketing
7. Implement `run_reconstruction()` — save to `timeline_reconstruction/timeline.json`
8. Test: `python -m timeline_reconstruction.reconstruct` → verify chronological order

---

## Dependencies

Only `networkx` is needed (already in `requirements.txt`). All other logic is pure Python stdlib (`json`, `datetime`, `collections`, `pathlib`, `math`).

No new packages needed.

---

## After All 3 Are Done → Next Steps

1. **Wire into API:** Update `api/main.py` to import from the 3 new folders and serve the cached JSON files
2. **LLM Narrator:** Build `llm_narrator/` that reads all 3 JSON outputs → feeds to Gemini → saves `cache/insights.json`
3. **Frontend:** Update the React dashboard to visualize the structured outputs
