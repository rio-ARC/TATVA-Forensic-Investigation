from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from ..insights.graph_insights import (
    get_graph_payload, get_suspects, get_alerts, get_timeline, get_summary
)
from ..insights.insight_schema import (
    GraphPayload, SuspectDetail, TransactionAlert, TimelineEvent, GraphSummary
)

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
    """Returns the full unified graph."""
    return get_graph_payload()

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
