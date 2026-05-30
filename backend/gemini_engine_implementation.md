# GEMINI ENGINE IMPLEMENTATION PLAN

## Objective

The Gemini Engine is the final intelligence layer of the forensic investigation platform.

All previous layers are responsible for:

* Extracting entities
* Building relationships
* Resolving identities
* Creating the unified graph
* Generating graph analytics

The Gemini Engine consumes these analytical outputs and converts them into a human-readable investigation report.

---

# Position in Overall Architecture

```text
Raw Inputs
    │
    ▼
Preprocessing Layer
(FIR, CDR, GPS, Email, Banking)
    │
    ▼
Entity Resolution Layer
    │
    ▼
Graph Integration Layer
    │
    ▼
Neo4j Memory Layer
    │
    ▼
Graph Summary
Rule Validation
Timeline Reconstruction
    │
    ▼
Gemini Engine
    │
    ▼
Investigation Report
```

---

# Inputs to Gemini Engine

The Gemini Engine does not interact directly with:

* FIRs
* CDRs
* GPS Logs
* Emails
* Transactions

Those are already processed.

Instead it receives:

---

## graph_summary.json

Generated from Neo4j.

Contains:

* Important entities
* Important locations
* Network statistics
* Highly connected nodes

Example:

```json
{
    "top_entities": [],
    "top_locations": [],
    "network_statistics": {}
}
```

---

## rule_validation.json

Generated from graph analytics.

Contains:

* Suspicious activity alerts
* Fraud indicators
* Communication anomalies
* Financial anomalies

Example:

```json
{
    "alerts": []
}
```

---

## timeline.json

Generated from graph traversal.

Contains chronological reconstruction.

Example:

```json
{
    "events": []
}
```

---

# Folder Structure

```text
Gemini_Engine/
│
├── inputs/
│   ├── graph_summary.json
│   ├── rule_validation.json
│   └── timeline.json
│
├── outputs/
│   └── investigation_report.md
│
├── gemini_client.py
└── main.py
```

---

# File Responsibilities

---

## gemini_client.py

Purpose:

Handle all communication with Gemini API.

Responsibilities:

* Initialize Gemini model
* Send prompts
* Receive responses
* Handle exceptions
* Return generated report

Example Function:

```python
generate_report(prompt)
```

Input:

```text
Prompt String
```

Output:

```text
Generated Investigation Report
```

---

## main.py

Purpose:

Orchestrates the complete Gemini workflow.

Responsibilities:

### Step 1

Load:

```text
graph_summary.json
rule_validation.json
timeline.json
```

---

### Step 2

Combine them into a single investigation context.

Example:

```python
context = {
    "graph_summary": graph_summary,
    "rule_validation": rule_validation,
    "timeline": timeline
}
```

---

### Step 3

Create a prompt.

Example:

```text
You are a forensic intelligence analyst.

Analyze the provided graph intelligence.

Generate:

1. Executive Summary
2. Key Suspects
3. Suspicious Activities
4. Timeline Narrative
5. Investigation Recommendations
```

---

### Step 4

Send prompt to Gemini.

```python
generate_report(prompt)
```

---

### Step 5

Receive generated report.

---

### Step 6

Save report.

Output:

```text
outputs/investigation_report.md
```

---

# Gemini Output Structure

The report should contain:

---

## Executive Summary

High-level case overview.

Example:

```text
The investigation indicates a coordinated
interaction between Rahul, Arjun and Vikram
through communication and financial activity.
```

---

## Key Individuals

Most relevant persons in the graph.

Example:

```text
Rahul
Arjun
Vikram
```

---

## Suspicious Activities

Explain alerts found by Rule Validation.

Example:

```text
ACC1001 distributed funds to multiple
accounts within a short period.
```

---

## Timeline Reconstruction

Convert raw events into a readable narrative.

Example:

```text
21:00 Rahul contacted Arjun.

21:15 Device activity observed near Park Street.

22:11 Financial transfer executed.
```

---

## Investigation Recommendations

Actionable next steps.

Example:

```text
Review CCTV near Park Street.

Obtain KYC information for ACC1001.

Analyze communication history of 9876543210.
```

---

# Execution Flow

```text
Load JSON Files
        │
        ▼

Build Investigation Context
        │
        ▼

Generate Prompt
        │
        ▼

Send To Gemini
        │
        ▼

Receive Report
        │
        ▼

Save investigation_report.md
```

---

# MVP Scope

For Version 1:

Implement only:

* gemini_client.py
* main.py
* investigation_report.md generation

Do not implement:

* Multi-agent systems
* Multiple Gemini calls
* Risk scoring modules
* Autonomous investigation planning

The goal is simple:

Convert graph-derived intelligence into a complete investigator-readable report using a single Gemini call.
