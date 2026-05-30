from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ── Visualization-ready models (used by GET /graph/render) ──────────────────

class RenderNode(BaseModel):
    """A node pre-adapted for direct consumption by react-force-graph-3d.
    All graph-semantic interpretation has already happened in the backend."""
    id: str
    label: str       # Human-readable display name
    type: str        # master_type: PERSON | PLACE | INFRASTRUCTURE | ENTITY
    sub_type: str    # entity_types[0]: ACCOUNT | CELL_TOWER | VEHICLE | …
    risk_score: float  # 0.0 for non-suspects, actual score for suspects

class RenderLink(BaseModel):
    """An edge pre-adapted for direct consumption by react-force-graph-3d."""
    source: str
    target: str
    type: str        # relation name: CALLED | TRANSFERRED_TO | …
    confidence: float

class GraphRenderPayload(BaseModel):
    nodes: List[RenderNode]
    links: List[RenderLink]

# ── Raw graph models (used by legacy GET /api/graph) ───────────────────────

class EntityDetail(BaseModel):
    master_id: str
    master_type: str
    entity_types: List[str]
    resolved_values: List[str]
    source_entities: List[str]

class RelationDetail(BaseModel):
    source: str
    target: str
    relation: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None
    confidence: float
    source_type: str

class GraphPayload(BaseModel):
    master_entities: List[EntityDetail]
    relations: List[RelationDetail]

class SuspectDetail(BaseModel):
    master_id: str
    name: str
    risk_score: float
    degree_centrality: float
    betweenness_centrality: float
    identifiers: List[str]
    entity_types: List[str]
    reasons: List[str]

class TransactionAlert(BaseModel):
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    amount: float
    timestamp: str
    alert_type: str  # e.g., "SMURFING", "CIRCULAR", "HIGH_VALUE", "ANOMALY"
    description: str
    risk_score: float

class TimelineEvent(BaseModel):
    timestamp: str
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    relation_type: str
    description: str
    confidence: float
    source_type: str

class GraphSummary(BaseModel):
    total_entities: int
    total_relations: int
    entity_type_counts: Dict[str, int]
    relation_type_counts: Dict[str, int]
    max_risk_suspect: Optional[str] = None
    total_alerts: int
