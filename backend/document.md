# Backend Data Stores Overview

The **TATVA‑Forensic‑Investigation** backend relies on three external data stores:

| Store | Purpose | Physical location | Primary schema |
|------|---------|-------------------|----------------|
| **Neo4j** | Graph database that holds the forensic knowledge graph (entities, relationships, risk scores, etc.) | Cloud‑hosted AuraDB instance (or local Neo4j server) – connection URL defined in `.env` as `NEO4J_URI` | **Node**: `MasterEntity` (properties: `master_id`, `master_type`, `resolved_values`, `entity_types`, …)<br>**Relationship**: `RELATION` (properties: `relation`, `confidence`, …) |
| **Upstash Redis** | Fast, in‑memory cache for graph‑insight payloads and auxiliary look‑ups (e.g., cache of computed insights, temporary geo‑lookup cache) | Managed Redis service (Upstash). URL in `.env` as `REDIS_URL` | Simple key‑value store. Typical keys: <br>`insights:<dataset>` → JSON string of `GraphPayload`<br>`geo_cache:<latlon>` → JSON of reverse‑geocode result |
| **Supabase (PostgreSQL)** | Relational store for case metadata, notes, evidence logs, audit trail, and user‑controlled tables | Supabase project (PostgreSQL 13+). Connection details in `.env` as `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | **Case** table (`case_id PK`, `title`, `description`, `investigator`, `metadata JSONB`)<br>**Note** table (`id PK`, `case_id FK`, `content`, `author`, `entity_ref`, `tags JSONB`)<br>**Evidence** table (`id PK`, `case_id FK`, `filename`, `file_type`, `file_hash`, `record_count`, `metadata JSONB`)<br>**AuditLog** table (`id PK`, `case_id FK`, `query_text`, `query_type`, `result_count`, `timestamp`) |

## 1️⃣ Neo4j – Graph Store

### What it stores
- **Master entities** (people, places, devices, etc.) with their resolved values.
- **Relationships** between entities (e.g., `OWNED_BY`, `TRANSACTION_WITH`).
- **Risk scores** are attached to suspects (a separate property on the node).

### How data gets in/out
| Direction | Code path | Description |
|-----------|-----------|--------------|
| **Load from Neo4j → Backend** | `backend/insights/graph_insights.py` → `graph_insights.compute_insights()` | Uses the official **Neo4j Python driver** (`neo4j` package). Cypher queries retrieve all nodes/relationships, then they are turned into `MasterEntity` and `Relation` objects. |
| **Write back (audit / updates)** | Not currently used for writes; the graph is read‑only for now. Future pipelines may use `session.run(<cypher>)` to push new edges. |

### Connection / API
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)
# Example query inside compute_insights()
with driver.session() as session:
    result = session.run("MATCH (n) RETURN n")
```

### Relevant Environment Variables (`.env`)
```dotenv
NEO4J_URI=bolt://<host>:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

---

## 2️⃣ Upstash Redis – Cache Layer

### What it stores
- **Serialized `GraphPayload`** (the full raw graph) under a cache key (`insights:<dataset>`).  
- **Geo‑cache** for Nominatim reverse‑geocode results (`geo_cache:<latlon>`).  
- Any temporary lookup tables that need sub‑second response (e.g., risk‑score map).

### How data gets in/out
| Direction | Code location | Description |
|-----------|---------------|--------------|
| **Write to cache** | `backend/db/redis_client.py` – `RedisClient.set_insights(payload_json)` | Stores JSON string with a TTL (default 15 min). |
| **Read from cache** | `backend/db/redis_client.py` – `RedisClient.get_insights()` | Returns cached JSON if present; otherwise triggers a fresh compute. |
| **Invalidate** | `backend/api/main.py` → `clear_insights_cache` endpoint | Calls `RedisClient.invalidate_insights()` which deletes the key. |

### Connection / API
```python
import redis

client = redis.from_url(os.getenv("REDIS_URL"))
# Example set
client.set("insights:UnifiedGraph", json_payload, ex=900)  # 15 min TTL
# Example get
cached = client.get("insights:UnifiedGraph")
```

### Relevant Environment Variables (`.env`)
```dotenv
REDIS_URL=redis://default:your_redis_password@my-upstash-redis.com:6379
```

---

## 3️⃣ Supabase (PostgreSQL) – Relational Store

### What it stores
- **Investigation cases** and associated metadata.  
- **Notes** and **evidence files** linked to a case.  
- **Audit log** of queries run against Neo4j/graph pipelines (used for compliance).

### How data gets in/out
| Direction | Code location | Description |
|-----------|---------------|--------------|
| **Create case** | `backend/api/main.py` → `create_case` endpoint → `PostgresClient.create_case` | Inserts a row into the `cases` table. |
| **Read case & enrich** | `get_case` endpoint → `PostgresClient.get_case`, `get_notes`, `get_evidence` | Performs `SELECT` queries and aggregates related rows. |
| **Add note / evidence** | `add_note`, `add_evidence` endpoints → respective `PostgresClient` methods | `INSERT` into `notes` / `evidence`. |
| **Audit log** | `PostgresClient.log_query` called from various endpoints (e.g., `/api/graph`) | Inserts a row into `audit_log`. |

### Connection / API
```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=int(os.getenv("POSTGRES_PORT")),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
```

### Relevant Environment Variables (`.env`)
```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tatva
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_pw
```

### Table schema (SQL – created by `alembic` migrations)
```sql
-- cases
CREATE TABLE cases (
    case_id      TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    investigator TEXT,
    metadata     JSONB,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- notes
CREATE TABLE notes (
    id          SERIAL PRIMARY KEY,
    case_id     TEXT REFERENCES cases(case_id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    author      TEXT DEFAULT 'analyst',
    entity_ref  TEXT,
    tags        JSONB,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- evidence
CREATE TABLE evidence (
    id          SERIAL PRIMARY KEY,
    case_id     TEXT REFERENCES cases(case_id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    file_type   TEXT DEFAULT 'csv',
    file_hash   TEXT,
    record_count INTEGER DEFAULT 0,
    metadata    JSONB,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- audit_log
CREATE TABLE audit_log (
    id           SERIAL PRIMARY KEY,
    case_id      TEXT,
    query_text   TEXT NOT NULL,
    query_type   TEXT NOT NULL,
    result_count INTEGER,
    timestamp    TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 4️⃣ Interaction Flow Summary (How the three stores work together)

1. **Client request** → Front‑end calls `/api/graph` (or `/graph/render`).
2. **Backend (`graph_insights.compute_insights`)**
   - Checks **Redis** for cached insights (`insights:UnifiedGraph`).
   - If miss → runs **Cypher** query against **Neo4j**, builds `master_entities` and `relations`.
   - Stores the fresh payload back into **Redis** (TTL).
3. **API returns JSON** to the front‑end, which renders the graph.
4. **Case‑management endpoints** (`/api/cases`, `/api/cases/{id}`) operate entirely on **Supabase PostgreSQL** via `PostgresClient`.
5. **Audit log** uses the same PostgreSQL connection; each request that hits Neo4j also logs a tiny row (`query_type=graph_fetch`, etc.) for traceability.

---

## 5️⃣ Where to Find the Code Implementations

| Store | Module | Key functions |
|-------|--------|---------------|
| **Neo4j** | `backend/insights/graph_insights.py` | `compute_insights()`, `get_suspects()`, `get_alerts()`, `get_timeline()`, `get_summary()` |
| **Redis** | `backend/db/redis_client.py` | `get_insights()`, `set_insights()`, `invalidate_insights()`, `get_stats()` |
| **Supabase (PostgreSQL)** | `backend/db/postgres_client.py` | `list_cases()`, `create_case()`, `get_case()`, `add_note()`, `add_evidence()`, `log_query()` |

---

## 6️⃣ Quick Checklist for Developers

- **Environment** – verify `.env` contains correct URIs/credentials for all three stores.
- **Migrations** – run `alembic upgrade head` after schema changes.
- **Redis TTL** – default 15 min; adjust in `RedisClient.set_insights` if required.
- **Neo4j read‑only** – current code only reads; make sure the AuraDB user has `READ` privileges.
- **Supabase permissions** – API key is embedded in the PostgreSQL connection; ensure the Supabase role has `INSERT/SELECT` on the case tables.

---

*End of Document*
