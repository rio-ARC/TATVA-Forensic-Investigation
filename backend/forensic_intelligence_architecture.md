# TATVA: Unified Forensic Intelligence Knowledge Graph Platform

## Vision

Traditional investigations suffer from fragmented evidence spread across multiple sources:

* FIR Reports
* Call Detail Records (CDR)
* GPS/Location Data
* Emails & Social Communications
* Banking Transactions

Investigators must manually correlate these datasets to discover relationships, timelines, and suspicious activities.

TATVA aims to automate this process by transforming heterogeneous forensic evidence into a unified knowledge graph capable of generating actionable investigative intelligence.

---

# System Architecture

```text
RAW DATA SOURCES
        │
        ▼
PREPROCESSING LAYER
(FIR / CDR / GPS / EMAIL / BANK)
        │
        ▼
STANDARDIZED GRAPH OBJECTS
(Entities + Relations)
        │
        ▼
ENTITY RESOLUTION LAYER
        │
        ▼
GRAPH INTEGRATION LAYER
        │
        ▼
UNIFIED KNOWLEDGE GRAPH
        │
        ▼
NEO4J MEMORY LAYER
        │
        ├─────────────► Graph Summary Module
        │
        ├─────────────► Entity Profile Generator
        │
        ├─────────────► Rule Validation Engine
        │
        └─────────────► Timeline Reconstruction
                                │
                                ▼
                      LLM Investigation Engine
                                │
                                ▼
                    Investigator Intelligence Report
```

---

# Phase 1: Data Ingestion Layer

Purpose:

Accept forensic evidence from multiple independent sources.

Supported Sources:

### FIR

Input:

```text
Natural language complaint reports
```

Example:

```text
Rahul met Arjun at Park Street.
```

---

### Call Detail Records

Input:

```csv
caller_number,receiver_number,timestamp,duration
```

Provides:

* Communication patterns
* Contact networks
* Tower associations

---

### GPS Data

Input:

```csv
device_id,latitude,longitude,timestamp
```

Provides:

* Movement reconstruction
* Co-location analysis
* Route intelligence

---

### Emails / Social Data

Input:

```text
Raw email messages
Chat logs
Social media exports
```

Provides:

* Digital communications
* Social relationships
* Planning activities

---

### Banking Transactions

Input:

```csv
sender_acc,receiver_acc,amount,timestamp
```

Provides:

* Financial trails
* Money movement
* Fraud indicators

---

# Phase 2: Preprocessing Layer

Each source has its own preprocessor.

Examples:

```text
fir.py
cdr.py
gps.py
socials.py
transaction.py
```

Output Format:

```json
{
  "entities": [],
  "relations": []
}
```

Every source is converted into a common graph format.

This standardization is essential for downstream integration.

---

# Phase 3: Entity Resolution Layer

Purpose:

Resolve multiple identifiers belonging to the same real-world entity.

Example:

```text
Rahul
9876543210
rahul@gmail.com
ANDROID_001
ACC1001
```

All may belong to:

```text
Rahul Sen
```

Entity resolution creates:

```text
MASTER_ENTITY
```

that represents the real-world individual.

---

## Identity Sources

Resolution may occur through:

### Direct Matching

Examples:

```text
same phone number
same email
same account
```

---

### Investigator Annotation

Example:

```json
{
    "person":"Rahul Sen",
    "phone":"9876543210",
    "email":"rahul@gmail.com",
    "account":"ACC1001",
    "device":"ANDROID_001"
}
```

This becomes high-confidence identity evidence.

---

### Future Extensions

* Fuzzy Matching
* Alias Resolution
* Face Recognition Mapping
* SIM Ownership Data
* Contact Book Analysis

---

# Phase 4: Graph Integration Layer

Purpose:

Merge all resolved entities into a unified graph.

Before Integration:

```text
Rahul
9876543210
rahul@gmail.com
ACC1001
```

After Integration:

```text
MASTER_RAHUL
```

All relationships now point to the master node.

Example:

```text
MASTER_RAHUL
      │
      ├── CALLED
      ├── EMAILED
      ├── TRANSFERRED_MONEY
      ├── VISITED
      └── CO_LOCATED_WITH
```

---

# Phase 5: Neo4j Memory Layer

Purpose:

Persist the unified graph.

Neo4j acts as:

```text
Investigation Memory
```

Responsibilities:

* Graph storage
* Relationship indexing
* Fast traversal
* Graph analytics
* Temporal querying

---

# Why Neo4j Exists

Without Neo4j:

```text
JSON
↓
Manual Traversal
↓
Slow Processing
```

With Neo4j:

```text
Graph Storage
↓
Cypher Queries
↓
Instant Graph Exploration
```

Neo4j stores knowledge.

It does not perform forensic reasoning.

---

# Phase 6: Graph Summary Module

Purpose:

Generate a high-level overview of the investigation graph.

Outputs:

### Network Statistics

* Total entities
* Total relations
* Most connected entities

---

### Key Individuals

Examples:

```text
Most active caller
Most connected suspect
Most active account
```

---

### Key Locations

Examples:

```text
Most visited location
Frequent meeting spot
```

---

Output:

```json
{
    "top_entities": [],
    "top_locations": [],
    "network_statistics": {}
}
```

---

# Phase 7: Entity Profile Generator

Purpose:

Generate a complete profile for every person.

Example:

```json
{
    "person":"Rahul Sen",
    "phones":[...],
    "emails":[...],
    "accounts":[...],
    "devices":[...],
    "locations":[...],
    "risk_score":0.87
}
```

Benefits:

* Investigator dashboard
* Suspect profiling
* Evidence aggregation

---

# Phase 8: Rule Validation Engine

Purpose:

Detect suspicious investigative patterns.

---

## Financial Rules

Examples:

### Smurfing

```text
Multiple transfers
below threshold
within short duration
```

---

### Mule Account Detection

```text
Large inflow
Immediate outflow
```

---

## Communication Rules

Examples:

### Call Burst

```text
High call frequency
within short period
```

---

### Hub Detection

```text
Single entity connected to many others
```

---

## Location Rules

Examples:

### Rendezvous Detection

```text
Multiple persons
same location
same time window
```

---

### Escape Route Analysis

```text
Movement immediately after event
```

---

Output:

```json
{
    "rule":"RENDEZVOUS",
    "confidence":0.92
}
```

---

# Phase 9: Timeline Reconstruction

Purpose:

Transform graph events into investigative timelines.

Investigators think in timelines rather than graphs.

---

Input:

```text
Email
Call
GPS Event
Transaction
```

---

Output:

```text
20:00 Email Sent

21:05 Phone Call

21:15 GPS Movement

22:11 Money Transfer
```

---

Timeline Phases:

### Planning Phase

Before incident

### Execution Phase

During incident

### Post-Incident Phase

After incident

---

# Phase 10: LLM Investigation Engine

Purpose:

Convert graph intelligence into human-readable reports.

Inputs:

* Graph Summary
* Entity Profiles
* Rule Validation Results
* Timeline Reconstruction

---

Outputs:

### Executive Summary

```text
What happened?
```

---

### Key Persons

```text
Who is important?
```

---

### Key Evidence

```text
What supports suspicion?
```

---

### Timeline Narrative

```text
How events unfolded?
```

---

### Threat Assessment

```text
Who should be investigated first?
```

---

# Future Enhancements

## Graph Data Science

* PageRank
* Betweenness Centrality
* Community Detection
* Shortest Path

---

## Link Prediction

Predict hidden relationships.

Example:

```text
Rahul ↔ Vikram
```

not directly observed but statistically likely.

---

## Graph Neural Networks

Applications:

* Fraud Detection
* Criminal Network Analysis
* Suspicious Entity Scoring
* Risk Prediction

---

## Multi-Agent Investigation System

Future agents:

### Communication Agent

Analyzes calls, emails, chats.

### Financial Agent

Analyzes transactions.

### Mobility Agent

Analyzes GPS and movement.

### Correlation Agent

Combines all evidence sources.

### Report Agent

Generates final intelligence report.

---

# Final Objective

Transform fragmented forensic evidence into connected investigative intelligence.

The system should not merely store evidence.

It should help investigators discover:

* Hidden relationships
* Suspicious behaviors
* Financial trails
* Communication networks
* Co-location events
* Event timelines
* High-risk entities

ultimately reducing investigative effort and improving intelligence discovery.
