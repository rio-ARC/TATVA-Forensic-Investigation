# TATVA | Advanced Digital Forensics & Graph Intelligence Platform

TATVA is a state-of-the-art, multi-dimensional digital forensics and intelligence synthesis platform designed for law enforcement, corporate security directors, and financial auditors. It dynamically ingests messy, heterogeneous evidence payloads (such as call detail records, banking transfers, tower coordinates, emails, and unstructured police reports), resolves entity duplication, maps interactive 3D knowledge graphs, and automatically validates risk profiles using custom forensic heuristics and Gemini-powered LLM analysis.

---

## 🚀 Key Forensic Pillars & Pipeline Architecture

TATVA automates the transition from raw digital evidence to courtroom-ready intelligence dossier reports. The pipeline is constructed of five core layers:

```
Case File Intake
      ↓ (Dynamic Schema Mapping via LLM / Heuristics)
Deterministic Preprocessors (CDR, Bank TXN, GPS towers, Emails, FIR)
      ↓ (Universal Canonical Schema Mapping)
Entity Resolution & Graph Integration
      ↓ (Merged Master Nodes / Temporal Links)
Neo4j Graph Database (AuraDB) & In-Memory Centrality Engine (NetworkX)
      ↓ (Degree/Betweenness Centrality & Risk Score Calculation)
Risk & Causality Validation (Smurfing, Circular Fund Cycles, Co-locations)
      ↓ (Gemini Forensic Dossier narrative generation)
Interactive Visualization & Dossier PDF Export (react-force-graph-3d + jsPDF)
```

### 1. Dynamic Schema intake (LLM & Heuristic Hybrid)
Digital evidence logs collected from service providers or seized hardware are rarely structured cleanly. TATVA resolves this:
* **Dynamic Column Alignment**: Automatically maps variations (e.g. `acc_num`, `receiver_account`, `tx_from`) to canonical schemas.
* **Intelligent Failback**: Routes unstructured plain text (like the First Information Report - FIR) through customized Spacy NLP classifiers to extract suspect aliases, emails, and coordinates dynamically.

### 2. Multi-Dimensional Preprocessors
Converts evidence categories into unified, standardized schema formats:
* **Call Detail Records (CDR)**: Resolves sender/receiver numbers, call durations, and cell-tower IDs.
* **Bank Transactions (BANK_TXN)**: Tracks cash transfers, amounts, dates, and account identifiers.
* **Geolocation Logs (GPS/Tower)**: Synthesizes cell-tower mapping and coordinates to trace suspect proximity.
* **Email Exchanges (EMAIL)**: Captures network communication links and timestamps.

### 3. Entity Resolution & Graph Integration
Eliminates duplicates by performing strict cross-reference resolution:
* Links multiple source nodes (e.g. a suspect's phone number, bank account, and physical tracker ID) under a single **Master Person Entity** node.
* Combines spatial, conversational, and transaction edges into a cohesive unified graph structure.

### 4. Graph Centrality & Risk Intelligence Engine
Runs real-time graph algorithms (using **NetworkX**) and rules engines to score threats:
* **Degree & Betweenness Centrality**: Evaluates node dominance to isolate key information brokers, main suspects, and orchestrators.
* **Advanced Heuristics**: Automatically flags indicators of crime:
  * **Smurfing (Fund Splitting)**: Multiple transactions split into smaller volumes (under 10,000 INR) within a narrow window.
  * **Circular Money Flows**: Fund routing loops that return money to the originator.
  * **Co-Location Patterns**: Overlaps where multiple suspects connect to the same tower within identical time blocks.

### 5. Gemini Forensic Dossier & PDF Export
Synthesizes numerical outputs, timelines, and suspect profiles into highly structured human-readable text:
* Generates narrative descriptions of the timeline.
* Produces recommendations for investigators (e.g. "Cross-reference security footage at Park Street between 20:45 and 21:15").
* Exports a multi-page, polished PDF dossier report directly from the client.

---

## 🛠️ Technology Stack

### Frontend (Client Portal)
* **Core**: React 18, TypeScript, TailwindCSS
* **Interactive Visualization**: `react-force-graph-3d` (Three.js/WebGL WebGL rendering of complex relationships)
* **Dossier Compilation**: `jsPDF` (Custom structured rendering of multi-page forensic reports)

### Backend (Forensic Core API)
* **Framework**: FastAPI (Python 3.10+)
* **Graph Computation**: NetworkX (Topological centralities, simple cycles, and degrees)
* **NLP Integration**: SpaCy (Custom extraction models for unstructured reports)
* **AI Model**: Google Gemini API (`gemini-2.5-flash`)

### Persistence & Caching
* **Relational Core**: PostgreSQL (Supabase backend for structured Case, Notes, and Upload registry metadata)
* **Knowledge Graph**: Neo4j AuraDB (Enterprise Cypher query execution)
* **Caching**: Upstash Redis (High-speed caching of compiled insights and payloads)

---

## 📂 Project Structure

```
TATVA-Forensic-Investigation/
├── backend/
│   ├── api/                     # FastAPI core endpoints and routes
│   ├── analysis/                # Graph Summary, Timeline, Risk Engines
│   ├── db/                      # Neo4j Client, PostgreSQL (Supabase) integration
│   ├── db_helper/               # Cypher mapping adapters
│   ├── Gemini_Engine/           # AI narrative generation engines
│   ├── Graph_Integration_Layer/ # Entity resolution and canonical preprocessors
│   ├── insights/                # API caching and schema decorators
│   ├── preprocessor/            # Deterministic CDR/GPS/Email/FIR parsers
│   └── uploads/                 # Case-specific evidence vault storage
├── frontend/
│   ├── src/
│   │   ├── components/          # ForceGraphViewer, PDF Export Modals
│   │   ├── pages/               # Case Files, dashboard, timeline page
│   │   ├── hooks/               # Live log simulators
│   │   └── types/               # Type checking schemas
└── jumbled_test_input/          # Unstructured testing logs
```

---

## ⚡ Setup & Execution

### 1. Environment Configurations
Configure the backend environmental variables in `backend/.env`:
```ini
# Neo4j Settings
NEO4J_URI=neo4j+ssc://your-aura-db-uri.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Supabase PostgreSQL Settings
SUPABASE_DB_URL=postgresql://postgres:your-supabase-db@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Redis Settings
REDIS_HOST=your-upstash-redis.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# AI Model Keys
GEMINI_API_KEY=AIzaSy...
```

### 2. Backend Execution
Activate your Python virtual environment and run the server:
```bash
cd backend
python -m venv env
# Windows:
env\Scripts\activate
# Linux/macOS:
source env/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Launch API
uvicorn api.main:app --reload
```

### 3. Frontend Execution
Install dependencies and run Vite's development server:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the TATVA portal.
