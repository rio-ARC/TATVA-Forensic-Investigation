# 🧬 TATVA Data Understanding Layer: LLM Preprocessor

Welcome to the **TATVA Data Understanding Layer**, an advanced, resilient preprocessing gateway powered by **Gemini 2.5 Flash** (with automatic, structural heuristic offline fallback).

---

## 🗺️ Architectural Context

Traditionally, ingestion pipelines expect strict canonical column names. If an investigator uploads a file where the phone headers are `from_mobile` instead of `caller_number`, the pipeline breaks. 

The **Data Understanding Layer** acts as an intelligent shield:

```
Investigator Upload (Messy File)
               │
               ▼
   [ Data Understanding Layer ]
               │
               ├─► Has GEMINI_API_KEY? ──► [ Gemini 2.5 Flash Classifier ]
               │                                       │
               └─► Offline / Keyless? ──► [ Heuristic Header Matcher ]
                                                       │
                                                       ▼
                                         [ Canonical Schema Mapper ]
                                                       │
                                                       ▼
                                         [ Normalized CSV Persistence ]
                                                       │
                                                       ▼
                                         [ Deterministic Preprocessor ]
                                                       │
                                                       ▼
                                             [ Unified Graph Data ]
```

---

## 📂 Subsystem Structure

The module is self-contained under `backend/llm_preprocessor/`:

*   `__init__.py`: Makes the module importable as a clean Python package.
*   `llm_preprocessor.py`: The core orchestrator. Classifies files, executes mapping, normalizes tables via `pandas`, and executes deterministic downstream modules.
*   `prompt_templates.py`: Curates specialized system instructions forcing Gemini to output strict JSON schemas.
*   `samples/`:
    *   `sample_1.csv`: A messy Call Detail Record (CDR) dump with non-canonical headers (`from_mobile`, `to_mobile`, `duration_sec`, etc.).
    *   `sample_2.csv`: A messy Bank Transaction dump with non-canonical headers (`source_account_no`, `destination_account_no`, `transfer_val`, etc.).
*   `preprocessed_output/`: Folder containing the normalized, canonical CSV files produced by the pipeline.

---

## ⚙️ How It Works

### 1. Classification & Column Mapping
When a raw evidence file is uploaded, the preprocessor reads the filename, columns, and first 3 sample lines of data. It queries Gemini 2.5 Flash to determine:
- **`file_type`**: One of the 5 canonical types (`CDR`, `GPS`, `BANK`, `EMAIL`, `FIR`).
- **`column_mapping`**: Dictionary mapping our canonical columns to the raw columns.

### 2. Tabular Normalization
Using the column mapping, `pandas` normalizes the raw DataFrame to match standard canonical schemas:

| Canonical Type | Canonical Columns | Fallbacks / Defaults |
| :--- | :--- | :--- |
| **`CDR`** | `caller_number`, `receiver_number`, `timestamp`, `duration`, `call_type`, `tower_id` | `call_type` $\rightarrow$ `"VOICE"`<br>`tower_id` $\rightarrow$ `"TWR_UNKNOWN"` |
| **`GPS`** | `device_id`, `latitude`, `longitude`, `timestamp`, `accuracy`, `speed`, `source` | `accuracy` / `speed` $\rightarrow$ `0.0`<br>`source` $\rightarrow$ `"gps_analysis"` |
| **`BANK`** | `sender_acc`, `receiver_acc`, `amount`, `timestamp`, `txn_type`, `location` | `txn_type` $\rightarrow$ `"TRANSFER"`<br>`location` $\rightarrow$ `"Unknown"` |

### 3. Downstream Bridging
Once the file is saved as a canonical CSV in the `preprocessed_output/` folder, it is immediately routed to the corresponding preprocessor:
- `CDR` $\rightarrow$ [`preprocessor.CallDetailsRecord.cdr.preprocess_cdr`](file:///e:/TATVA-Forensic-Investigation/backend/preprocessor/CallDetailsRecord/cdr.py)
- `GPS` $\rightarrow$ [`preprocessor.GPS_Preprocessed.gps.preprocess_gps`](file:///e:/TATVA-Forensic-Investigation/backend/preprocessor/GPS_Preprocessed/gps.py)
- `BANK` $\rightarrow$ [`preprocessor.bank_transaction_pipeline.main.preprocess_transaction`](file:///e:/TATVA-Forensic-Investigation/backend/preprocessor/bank_transaction_pipeline/main.py)

---

## 🛡️ Offline / Keyless Resilience: Heuristic Fallback Mode

To ensure the platform operates seamlessly in offline, secure, or keyless deployments, we designed a **Structural Heuristic Classifier** fallback:
- If `GEMINI_API_KEY` is not present, the system immediately runs a keyword-matching heuristic.
- It scans raw header names for domain-specific indicators (e.g. `"lat"`, `"lon"`, `"acc"`, `"caller"`, `"transfer"`, `"amount"`).
- It generates the canonical column mappings and defaults automatically, allowing successful imports without an active internet connection or API costs.

---

## 🚀 Running Verification Tests

To verify that the Data Understanding Layer correctly processes raw forensic files, run:

```bash
cd backend
python -m llm_preprocessor.llm_preprocessor
```

The script will ingest the messy raw files in `samples/`, output the normalized files in `preprocessed_output/`, and run them through downstream engines, logging the resulting entities and relationships.
