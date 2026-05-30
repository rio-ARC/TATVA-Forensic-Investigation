# Bank Transaction Preprocessing Pipeline

## Objective

This module preprocesses raw bank transaction data and converts fragmented financial transaction logs into graph-ready intelligence for forensic investigation and knowledge graph reconstruction.

The preprocessing pipeline performs:

- Transaction normalization
- Entity extraction
- Behavioural feature engineering
- Suspicious activity analysis
- Anomaly detection
- Knowledge graph construction

---

# Pipeline Architecture

```text
Raw Transactions
        ↓
Data Cleaning & Normalization
        ↓
Entity Extraction
        ↓
Feature Engineering
        ↓
Anomaly Detection
        ↓
Knowledge Graph Construction
        ↓
Graph-ready JSON Output
```

---

# Data Cleaning & Normalization

The preprocessing layer performs:

- Duplicate transaction removal
- Missing value handling
- Timestamp normalization
- Invalid amount correction
- Account ID standardization

Example:

```text
acc1001 → ACC1001
-5000   → 5000
```

This ensures consistency before graph generation.

---

# Extracted Entities

The pipeline extracts the following entities from raw transaction logs:

```text
- Sender Accounts
- Receiver Accounts
- Devices
- Locations
- Transaction Types
- Financial Relationships
```

These entities later become graph nodes and relationships.

---

# Features Extracted

Behavioural and forensic intelligence features:

```text
- txn_frequency
- avg_amount
- night_txn_ratio
- unique_receivers
- burst_transfer_score
- high_value_transfer_score
- suspicious_activity_ratio
```

Example feature vector:

```text
ACC1001 →
[
  txn_frequency = 24,
  avg_amount = 8200,
  night_txn_ratio = 0.72,
  unique_receivers = 11
]
```

These features are later used for:

- Graph analytics
- Risk scoring
- GNN intelligence layer
- Behavioural anomaly analysis

---

# Suspicious Pattern Detection

The anomaly detection engine identifies:

```text
- Burst Transactions
- High-value Transfers
- Night-time Transaction Activity
- Rapid Money Flow
- Circular Transaction Chains
- Coordinated Transfer Behaviour
- Suspicious Relationship Expansion
```

Example:

```text
ACC1001
    ↓
5 transfers within 2 minutes
    ↓
Flagged as Burst Transaction Activity
```

Each suspicious entity receives:

```text
- reason
- evidence
- risk_score
```

This supports explainable forensic analysis.

---

# Knowledge Graph Construction

Each bank account becomes a graph node.

```text
(Account_A)
```

Each transaction becomes a graph edge.

```text
(Account_A)
      │
TRANSFERRED_TO
      │
      ▼
(Account_B)
```

Each edge stores metadata:

```text
- amount
- timestamp
- transaction_type
- location
- risk_score
```

The generated graph structure supports:

- Neo4j integration
- Graph analytics
- GNN inference
- Temporal reconstruction
- Explainable investigation workflows

---

# Output Files

The preprocessing pipeline exports:

```text
data/processed/

├── cleaned_transactions.csv
├── suspicious_transactions.json
├── nodes.json
└── edges.json
```

---

# Graph-ready JSON Example

## Node Example

```json
{
  "id": "ACC1001",
  "type": "ACCOUNT",
  "risk_score": 0.82,
  "features": {
    "txn_frequency": 24,
    "avg_amount": 8200
  }
}
```

## Edge Example

```json
{
  "source": "ACC1001",
  "target": "ACC2001",
  "relation": "TRANSFERRED_TO",
  "amount": 50000,
  "timestamp": "2026-05-22 22:11:00"
}
```

---

# Technologies Used

```text
- Python
- Pandas
- NumPy
- NetworkX
- JSON
- Graph-based Data Modelling
```

---

# System Integration

This preprocessing module directly integrates with:

```text
- Knowledge Graph Layer
- Graph Analytics Layer
- GNN Intelligence Engine
- Temporal Reconstruction Engine
- Explainability Layer
- Investigator Dashboard
```

---

# Future Scope

Future enhancements may include:

```text
- Neo4j Database Integration
- GNN-based Fraud Prediction
- Temporal Sequence Analysis
- Cross-source Entity Resolution
- Explainable AI Risk Attribution
- Multi-bank Transaction Correlation
- Real-time Streaming Transaction Analysis
```

---

# Core Forensic Objective

```text
RAW FINANCIAL TRANSACTIONS
            ↓
CONNECTED FORENSIC INTELLIGENCE
            ↓
EXPLAINABLE KNOWLEDGE GRAPH ANALYSIS
```