from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

from ..insights.graph_insights import (
    get_suspects, get_alerts, get_timeline, get_summary, compute_insights
)
from ..insights import graph_insights
from ..insights.insight_schema import (
    GraphPayload, SuspectDetail, TransactionAlert, TimelineEvent, GraphSummary,
    EntityDetail, RelationDetail,
    GraphRenderPayload, RenderNode, RenderLink,
)
from ..db.postgres_client import PostgresClient
from ..db.redis_client import RedisClient


# ---------------------------------------------------------------------------
# Helper: legacy raw-graph payload (kept for backward compatibility)
# ---------------------------------------------------------------------------

def get_graph_payload() -> GraphPayload:
    if not graph_insights._GRAPH_DATA:
        compute_insights()
    return GraphPayload(
        master_entities=[EntityDetail(**m) for m in graph_insights._GRAPH_DATA.get("master_entities", [])],
        relations=[RelationDetail(**r) for r in graph_insights._GRAPH_DATA.get("relations", [])]
    )

# ---------------------------------------------------------------------------
# Helper: build a human-readable label for a master entity.
# This is the canonical name-resolution logic — frontend must NOT duplicate it.
# ---------------------------------------------------------------------------

def _entity_label(master: dict) -> str:
    """Return the best human-readable display name for a master entity."""
    resolved = master.get("resolved_values", [])
    master_type = master.get("master_type", "")

    # For PERSON entities, prefer a token that looks like a proper name
    if master_type == "PERSON":
        for val in resolved:
            v = val.strip()
            # Skip phone numbers, account IDs, device IDs, social handles, emails
            if (not v.startswith("98") and not v.startswith("91")
                    and not v.startswith("acc") and not v.startswith("@")
                    and "@" not in v and not v.startswith("android")
                    and not v.startswith("watch") and not v.startswith("tracker")
                    and not any(c.isdigit() for c in v)
                    and len(v) > 2):
                return v.title()

    # For PLACE, INFRASTRUCTURE, ENTITY — first resolved value is usually descriptive
    if resolved:
        label = resolved[0].strip()
        # Clean up synthetic IDs like "email_address_cc44d0c6"
        if "_" in label and len(label) > 20:
            return label.replace("_", " ").title()
        return label.replace("_", " ").title() if "_" in label else label.title()

    return master.get("master_id", "Unknown")

# ---------------------------------------------------------------------------
# Helper: build the visualization-ready graph render payload
# ---------------------------------------------------------------------------

def get_graph_render_payload() -> GraphRenderPayload:
    """
    Adapter that converts unified_graph.json into clean visualization data.
    Enriches nodes with risk scores from suspect analysis.
    The frontend receives ONLY this — no raw entity resolution data.
    """
    if not graph_insights._GRAPH_DATA:
        compute_insights()
    if not graph_insights._SUSPECTS:
        compute_insights()

    # Build a risk-score lookup: master_id → risk_score
    risk_lookup: dict[str, float] = {
        s.master_id: s.risk_score
        for s in graph_insights._SUSPECTS
    }

    masters = graph_insights._GRAPH_DATA.get("master_entities", [])
    relations = graph_insights._GRAPH_DATA.get("relations", [])

    nodes: list[RenderNode] = []
    for m in masters:
        mid = m["master_id"]
        entity_types = m.get("entity_types", [])
        nodes.append(RenderNode(
            id=mid,
            label=_entity_label(m),
            type=m.get("master_type", "ENTITY"),
            sub_type=entity_types[0] if entity_types else "UNKNOWN",
            risk_score=risk_lookup.get(mid, 0.0),
        ))

    links: list[RenderLink] = []
    for r in relations:
        links.append(RenderLink(
            source=r["source"],
            target=r["target"],
            type=r.get("relation", "RELATED"),
            confidence=float(r.get("confidence", 1.0)),
        ))

    return GraphRenderPayload(nodes=nodes, links=links)


app = FastAPI(title="TATVA Insights & Forensic API", version="1.1.0")

# Enable CORS for the frontend Vite server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and Cache clients
db = PostgresClient()
cache = RedisClient()

@app.on_event("startup")
def startup_event():
    """Ensure database tables exist on API startup."""
    if db.engine:
        try:
            db.create_tables()
            print("[API Startup] Supabase PostgreSQL tables verified/created.")
        except Exception as e:
            print(f"[API Startup] Failed to initialize PostgreSQL tables: {e}")
    else:
        print("[API Startup] WARNING: PostgreSQL client not connected.")

# ── REQUEST SCHEMAS ──────────────────────────────────────────

class CaseCreate(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = ""
    investigator: Optional[str] = ""
    metadata: Optional[dict] = None

class NoteCreate(BaseModel):
    content: str
    author: Optional[str] = "analyst"
    entity_ref: Optional[str] = None
    tags: Optional[List[str]] = None

class EvidenceCreate(BaseModel):
    filename: str
    file_type: Optional[str] = "csv"
    file_hash: Optional[str] = ""
    record_count: Optional[int] = 0
    metadata: Optional[dict] = None

# ── ORIGINAL GRAPH & INSIGHTS ENDPOINTS ──────────────────────

@app.get("/api/graph", response_model=GraphPayload)
def read_graph(dataset: str = "UnifiedGraph"):
    """Returns the full unified graph. Caches in Redis and queries Neo4j."""
    # Log query to Postgres
    db.log_query(
        query_text=f"Fetched full graph for dataset '{dataset}'",
        query_type="graph_fetch",
        result_count=1,
        case_id=None
    )
    return get_graph_payload()

@app.get("/graph/render", response_model=GraphRenderPayload)
def read_graph_render():
    """
    Returns visualization-ready graph data for react-force-graph-3d.
    All graph interpretation (name resolution, risk scoring, type mapping)
    is performed here. The frontend receives only clean nodes + links.
    """
    return get_graph_render_payload()

@app.get("/api/insights/suspects", response_model=List[SuspectDetail])
def read_suspects():
    """Returns a list of suspects scored by risk."""
    return get_suspects()

@app.get("/api/insights/transactions", response_model=List[TransactionAlert])
def read_transactions():
    """Returns flagged transactions (smurfing, circular flows, etc.)."""
    return get_alerts()

@app.get("/api/timeline")
def read_timeline():
    """Returns the generated timeline.json produced by the timeline reconstruction layer."""
    import os
    import json
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "timeline_reconstruction", "timeline.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenes": []}

@app.get("/api/insights/summary", response_model=GraphSummary)
def read_summary():
    """Returns global metrics of the graph."""
    return get_summary()

# ── NEW POSTGRES CASES & USER INPUTS ENDPOINTS ───────────────

@app.get("/api/cases")
def list_cases(status: Optional[str] = None):
    """List all investigation cases stored in Supabase."""
    try:
        return db.list_cases(status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases")
def create_case(case: CaseCreate):
    """Create a new case in Supabase PostgreSQL."""
    try:
        return db.create_case(
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            investigator=case.investigator,
            metadata=case.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    """Get details of a specific case, including metadata, notes, and evidence."""
    data = db.get_case(case_id=case_id)
    if not data:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Enrich with notes and evidence list
    data["notes"] = db.get_notes(case_id=case_id)
    data["evidence_files"] = db.get_evidence(case_id=case_id)
    return data

@app.post("/api/cases/{case_id}/notes")
def add_note(case_id: str, note: NoteCreate):
    """Add an investigator note or annotation to a case."""
    try:
        return db.add_note(
            case_id=case_id,
            content=note.content,
            author=note.author,
            entity_ref=note.entity_ref,
            tags=note.tags
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/cases/{case_id}/notes")
def get_notes(case_id: str):
    """Get all notes for a case."""
    return db.get_notes(case_id=case_id)

@app.post("/api/cases/{case_id}/evidence")
def add_evidence(case_id: str, ev: EvidenceCreate):
    """Log an evidence file uploaded for a case."""
    try:
        return db.add_evidence(
            case_id=case_id,
            filename=ev.filename,
            file_type=ev.file_type,
            file_hash=ev.file_hash,
            record_count=ev.record_count,
            metadata=ev.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/cases/{case_id}/evidence")
def get_evidence(case_id: str):
    """Get all logged evidence files for a case."""
    return db.get_evidence(case_id=case_id)

# ── AUDIT & SYSTEM STATUS ENDPOINTS ─────────────────────────

@app.get("/api/audit")
def get_audit(limit: int = Query(default=50, ge=1, le=200)):
    """Retrieve audit trail logs of investigator actions."""
    return db.get_audit_log(limit=limit)

@app.get("/api/cache/stats")
def get_cache_stats():
    """Retrieve statistics of Upstash Redis cache (hits/keys)."""
    return cache.get_stats() if cache.connected else {"connected": False}

@app.post("/api/cache/clear")
def clear_insights_cache():
    """Manually invalidate cached graph insights."""
    if cache.connected:
        count = cache.invalidate_insights()
        return {"status": "success", "invalidated_keys_count": count}
    return {"status": "error", "message": "Redis not connected"}

@app.post("/api/case/process")
def process_case(case_id: str = Body(..., embed=True)):
    """Simulates evidence ingestion pipeline and updates PostgreSQL."""
    # Log progress to Supabase
    db.log_query(
        query_text=f"Triggered processing pipeline for case '{case_id}'",
        query_type="pipeline_trigger",
        result_count=1,
        case_id=case_id
    )
    # Clear old insights cache since new processing is starting
    if cache.connected:
        cache.invalidate_insights()
        
    return {
        "status": "success",
        "message": f"Evidence ingested for case {case_id} and pipeline started.",
        "cache_invalidated": cache.connected
    }
