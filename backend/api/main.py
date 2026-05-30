from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from ..insights.graph_insights import (
    get_suspects, get_alerts, get_timeline, get_summary, compute_insights
)
from ..insights import graph_insights
from ..insights.insight_schema import (
    GraphPayload, SuspectDetail, TransactionAlert, TimelineEvent, GraphSummary,
    EntityDetail, RelationDetail,
    GraphRenderPayload, RenderNode, RenderLink,
)

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


app = FastAPI(title="TATVA Insights API", version="1.0.0")

# Enable CORS for the frontend Vite server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/graph", response_model=GraphPayload)
def read_graph():
    """Returns the full unified graph (legacy raw format)."""
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

@app.get("/api/timeline", response_model=List[TimelineEvent])
def read_timeline():
    """Returns the temporal sequence of events across all sources."""
    return get_timeline()

@app.get("/api/insights/summary", response_model=GraphSummary)
def read_summary():
    """Returns global metrics of the graph."""
    return get_summary()

@app.post("/api/case/process")
def process_case():
    """Mock endpoint to simulate case processing pipeline."""
    return {"status": "success", "message": "Evidence ingested and pipeline started."}
