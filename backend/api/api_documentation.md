# TATVA — API Layer Documentation

This document describes the structure, updates, and newly registered endpoints created inside the `backend/api/` folder to support the **Risk Intelligence Engine** and end-to-end pipeline execution.

---

## 1. Directory Structure

```
backend/api/
├── __init__.py            # Module initialization
├── api_documentation.md   # [NEW] This documentation file
└── main.py                # [MODIFIED] FastAPI application core
```

---

## 2. Updates & Modifications in `main.py`

### A. End-to-End Pipeline Integration
Imported and integrated modular backend orchestrators from the analysis packages and Gemini Engine:
- `run_summary()` from `analysis.graph_summary.summarize`
- `run_reconstruction()` from `analysis.timeline_reconstruction.reconstruct`
- `run_validation_pipeline()` from `analysis.rule_validation.validate`
- `run_engine()` from `Gemini_Engine.main`

### B. Updated Endpoints
#### 1. Ingest & Process Case (`POST /api/case/process`)
- **Legacy Behavior**: Mock simulated PostgreSQL update.
- **Updated Behavior**: Sequentially triggers the **real end-to-end forensic processing and LLM report synthesis pipeline** in a single synchronous call.
- **Execution Flow**:
  1. Computes Graph Topology Summaries and Node Centralities (`run_summary`).
  2. Reconstructs Chronological Timeline Scenes (`run_reconstruction`).
  3. Executes Risk Intelligence Engine calculations (`run_validation_pipeline`).
  4. Triggers Gemini Report Synthesis (`run_engine`).
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Full TATVA pipeline successfully executed for case 'case_001'!",
    "report_path": "backend/Gemini_Engine/outputs/investigation_report.md",
    "cache_invalidated": true
  }
  ```

#### 2. Visual Render Payload (`GET /graph/render`)
- **Legacy Behavior**: Returned risk scores from the basic `graph_insights._SUSPECTS` map.
- **Updated Behavior**: Checks for premium `person_risk_profiles.json` output first, mapping precise time-decayed, confidence-weighted risk scores to graph nodes dynamically. Falls back to legacy suspects mapping safely on exception.

---

## 3. New REST Endpoints Created

### A. Person Risk Profiles (`GET /api/insights/risk-profiles`)
Retrieves the fully structured, explainable, and confidence-weighted risk assessment profiles for all resolved human actors.

- **Source File**: `backend/analysis/rule_validation/output/person_risk_profiles.json`
- **Response Schema Example**:
  ```json
  [
    {
      "person_id": "MASTER_b41353c7",
      "name": "Rahul Sen",
      "risk_score": 100.0,
      "risk_level": "CRITICAL",
      "confidence": 0.96,
      "graph_metrics": {
        "degree": 0.5217,
        "betweenness": 0.1074,
        "pagerank": 0.034
      },
      "triggered_rules": [
        "FIN_SMURFING",
        "COMM_DELETION_LANGUAGE",
        "TEMP_COLOCATION_TO_TRANSFER"
      ],
      "explanation": "Rahul Sen has been assigned a CRITICAL risk score of 100.0 (Confidence: 96%). The primary contributing factors include structuring transaction flows, physical meetings followed immediately by money movement...",
      "identifiers": [
        "rahul sen",
        "9876543210",
        "acc1001",
        "android_001"
      ],
      "entity_types": [
        "PERSON",
        "PHONE_NUMBER",
        "ACCOUNT",
        "DEVICE"
      ],
      "evidence": [
        {
          "person_id": "MASTER_b41353c7",
          "rule_code": "COMM_DELETION_LANGUAGE",
          "rule_name": "Deletion Language",
          "base_weight": 10.0,
          "confidence": 0.97,
          "source_reliability": 0.8,
          "time_decay": 0.7,
          "weighted_contribution": 5.43,
          "timestamp": "2026-05-22T19:45:00+05:30",
          "evidence": {
            "channel": "emailed",
            "target": "Arjun",
            "text_snippet": "Tonight's Operation - Final Plan",
            "matched_by": "forensic_signal"
          }
        }
      ],
      "timeline": [
        {
          "timestamp": "2026-05-22T19:45:00+05:30",
          "action": "EMAILED",
          "description": "Rahul Sen emailed Arjun -- Subject: Tonight's Operation - Final Plan",
          "confidence": 0.97,
          "source_type": "unknown"
        }
      ]
    }
  ]
  ```

### B. Relationship Risk Profiles (`GET /api/insights/relationship-profiles`)
Retrieves the risk assessment scores and supporting evidence descriptions for interactive, interacting pairs of entities (e.g. Rahul Sen ↔ Rajan Mehta).

- **Source File**: `backend/analysis/rule_validation/output/relationship_risk_profiles.json`
- **Response Schema Example**:
  ```json
  [
    {
      "entity_1_id": "MASTER_b41353c7",
      "entity_1": "Rahul Sen",
      "entity_2_id": "MASTER_d7c86824",
      "entity_2": "ACC2001",
      "risk_score": 19.8,
      "risk_level": "LOW",
      "interaction_counts": {
        "calls": 0,
        "messages": 0,
        "transfers": 1,
        "shared_devices": 0
      },
      "supporting_evidence": [
        "1 money transfer(s) totaling Rs.9,400"
      ],
      "confidence": 0.99,
      "explanation": "The connection between Rahul Sen and ACC2001 is classified as LOW RISK with a score of 19.8. Supporting indicators: 1 money transfer(s) totaling Rs.9,400."
    }
  ]
  ```
