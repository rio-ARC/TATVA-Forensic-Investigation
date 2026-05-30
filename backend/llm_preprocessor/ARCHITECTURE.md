# TATVA — Dynamic Schema Mapping Architecture

## Problem

The original preprocessors expected fixed canonical column names:

```
CDR:   caller_number, receiver_number, timestamp, duration
BANK:  sender_acc, receiver_acc, amount, timestamp
GPS:   device_id, latitude, longitude, timestamp
```

If an investigator uploaded a file with different names like `from_mobile`, `to_mobile`, `call_time`, `call_length` — the preprocessor failed.

---

## New Architecture

```
Investigator Upload (any CSV / XLSX / JSON / TSV / PDF / TXT)
         |
         v
[SchemaAnalyzer]  <-- schema_analyzer.py
   - Gemini 2.5 Flash (primary)
   - Structural heuristic classifier (fallback when offline/quota)
   - Returns: dataset_type, column_mapping, confidence
         |
         |--- confidence < 0.70 ----------> raise ValueError("UNSUPPORTED_SCHEMA")
         |
         v
    Structured?
    (CSV/XLSX/JSON/TSV)
         |                         |
        YES                        NO (PDF/TXT/FIR/CASE_NOTES)
         |                         |
         v                         v
[Router]                  [UnstructuredHandler]
   CDR       ---------->  CDRPreprocessor(file, mapping=...)
   BANK_TX   ---------->  BankTransactionPreprocessor(file, mapping=...)
   GPS       ---------->  GPSPreprocessor(file, mapping=...)
   CHAT_LOG  ---------->  SocialPreprocessor(file)
             ---------->  FIRPreprocessor(raw_text)
         |
         v
  Output contract (unchanged):
  {
    "entities": [...],
    "relations": [...]
  }
```

---

## LLM Responsibilities (strictly limited)

The LLM does ONLY:

1. **Dataset type detection** — CDR, BANK_TRANSACTION, GPS, CHAT_LOG, EMAIL, FIR, UNKNOWN
2. **Column mapping** — maps canonical field names to the actual raw column names in the file

The LLM does NOT:
- Extract entities
- Extract relations
- Parse data rows
- Generate graph structures

---

## Module Layout

```
backend/llm_preprocessor/
    canonical_schemas.py    -- Single source of truth: schemas, required/optional cols, defaults
    schema_analyzer.py      -- Gemini LLM + heuristic fallback for type detection + mapping
    schema_mapper.py        -- Pure pandas: applies column_mapping to rename raw -> canonical
    llm_preprocessor.py     -- Orchestrator: analyze -> route -> return graph
    __init__.py             -- Public exports

backend/preprocessor/
    CallDetailsRecord/cdr.py            -- Now accepts mapping=dict param
    GPS_Preprocessed/gps.py             -- Now accepts mapping=dict param
    bank_transaction_pipeline/
        main.py                         -- Now accepts mapping=dict param
        preprocessing/cleaner.py        -- Now accepts mapping=dict param, renames cols
```

---

## Canonical Schemas

### CDR
| Canonical | Required | Default |
|---|---|---|
| `caller_number` | yes | - |
| `receiver_number` | yes | - |
| `timestamp` | yes | - |
| `duration` | yes | - |
| `call_type` | no | `VOICE` |
| `tower_id` | no | `TWR_UNKNOWN` |

### BANK_TRANSACTION
| Canonical | Required | Default |
|---|---|---|
| `sender_acc` | yes | - |
| `receiver_acc` | yes | - |
| `amount` | yes | - |
| `timestamp` | yes | - |
| `txn_type` | no | `TRANSFER` |
| `location` | no | `Unknown` |

### GPS
| Canonical | Required | Default |
|---|---|---|
| `device_id` | yes | - |
| `latitude` | yes | - |
| `longitude` | yes | - |
| `timestamp` | yes | - |
| `accuracy` | no | `0.0` |
| `speed` | no | `0.0` |
| `source` | no | `gps_analysis` |

---

## Example — End to End

### Input file: `cdr_may.csv`

```csv
from_mobile,to_mobile,call_time,call_length,cell_tower
9876543210,9123456780,2026-05-22 20:30:00,120,TWR_001
```

### Gemini output (from SchemaAnalyzer)

```json
{
  "dataset_type": "CDR",
  "column_mapping": {
    "caller_number": "from_mobile",
    "receiver_number": "to_mobile",
    "timestamp": "call_time",
    "duration": "call_length",
    "tower_id": "cell_tower"
  },
  "confidence": 0.99
}
```

### Preprocessor call

```python
preprocess_cdr("cdr_may.csv", mapping={
    "caller_number": "from_mobile",
    "receiver_number": "to_mobile",
    "timestamp": "call_time",
    "duration": "call_length",
    "tower_id": "cell_tower"
})
```

The CDR preprocessor reads `row["from_mobile"]` via `row[col("caller_number")]`, fully transparent to the extraction logic.

---

## Confidence Threshold

`CONFIDENCE_THRESHOLD = 0.70`

If Gemini or heuristic confidence < 0.70, the pipeline raises:

```
ValueError: Confidence 0.45 below threshold 0.70 for 'mystery.csv'.
Detected type: UNKNOWN. Cannot proceed — schema unclear.
```

---

## Fallback Behaviour

| Condition | Behaviour |
|---|---|
| `GEMINI_API_KEY` present, quota OK | LLM classification |
| `GEMINI_API_KEY` present, rate-limited | Automatic heuristic fallback |
| No `GEMINI_API_KEY` | Heuristic fallback immediately |
| Heuristic confident | Proceeds normally |
| Both fail | Returns UNKNOWN, raises ValueError |

---

## Backward Compatibility

All existing callers pass through unchanged:

```python
# Still works (no mapping, canonical names already in file)
preprocess_cdr("cdr.csv")
preprocess_gps("gps.csv")
preprocess_transaction("transactions.csv")
```

No downstream changes to Entity Resolution, Graph Integration,
Timeline Reconstruction, Risk Scoring, or Neo4j ingestion.
