"""
llm_preprocessor/schema_analyzer.py
=====================================
Responsible ONLY for:
  1. Detecting the dataset type (CDR, BANK_TRANSACTION, GPS, FIR, ...)
  2. Producing a column_mapping from canonical names -> raw file column names

Does NOT extract entities, relations, or events.
Does NOT touch the data rows.

Uses Gemini 2.5 Flash when GEMINI_API_KEY is available.
Falls back to structural heuristics when offline or key is absent.

Returns a SchemaAnalysis dataclass:
{
    "dataset_type": "CDR",
    "column_mapping": {
        "caller_number": "source",
        "receiver_number": "destination",
        "timestamp": "call_time",
        "duration": "call_length"
    },
    "confidence": 0.95,
    "mode": "llm" | "heuristic"
}
"""

import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from .canonical_schemas import CANONICAL_SCHEMAS, CONFIDENCE_THRESHOLD

# Load env
load_dotenv(Path(__file__).parent.parent / ".env")

# ── Gemini setup (lazy — only imported if key is present) ──
_genai = None

def _get_genai():
    global _genai
    if _genai is not None:
        return _genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _genai = genai
        return _genai
    except Exception as e:
        print(f"[SchemaAnalyzer] Gemini import error: {e}")
        return None


# ──────────────────────────────────────────────────────────
# LLM PROMPT
# ──────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """
You are a forensic data analyst AI.

Your ONLY job is to:
1. Determine the dataset type of the uploaded file.
2. Map the raw column names to our canonical schema columns.

---

### SUPPORTED DATASET TYPES

| Type | Purpose |
|------|---------|
| CDR | Telecom call detail records between phone numbers |
| BANK_TRANSACTION | Financial wire transfers between bank accounts |
| GPS | Geographic location tracking logs for devices/vehicles |
| CHAT_LOG | WhatsApp, Telegram, or similar chat exports |
| EMAIL | Email communication logs |
| FIR | First information report or free-text complaint document |
| CASE_NOTES | Free-text investigator notes or reports |
| UNKNOWN | Cannot determine from provided data |

---

### CANONICAL SCHEMAS

CDR required: caller_number, receiver_number, timestamp, duration
CDR optional: call_type (default VOICE), tower_id (default TWR_UNKNOWN)

BANK_TRANSACTION required: sender_acc, receiver_acc, amount, timestamp
BANK_TRANSACTION optional: txn_type (default TRANSFER), location (default Unknown)

GPS required: device_id, latitude, longitude, timestamp
GPS optional: accuracy (default 0.0), speed (default 0.0), source (default gps_analysis)

CHAT_LOG required: sender, receiver, message, timestamp
EMAIL required: sender, recipient, subject, timestamp

---

### FILE INFORMATION

Filename: {filename}
Extension: {extension}
Detected columns / headers: {headers}

Sample rows (first 5):
{sample_rows}

---

### INSTRUCTIONS

- Analyze the column names and sample data semantically.
- Determine which dataset type this is.
- Map each canonical column name to the actual raw column name in the file.
- Only map columns that genuinely exist in the raw file.
- Do not invent mappings.
- For unstructured types (FIR, CASE_NOTES) set column_mapping to {{}}.
- Return ONLY a JSON object matching the schema below.

### RESPONSE FORMAT (strict JSON only, no markdown, no prose)

{{
  "dataset_type": "CDR",
  "column_mapping": {{
    "caller_number": "source",
    "receiver_number": "destination",
    "timestamp": "call_time",
    "duration": "call_length"
  }},
  "confidence": 0.95
}}
"""


# ──────────────────────────────────────────────────────────
# FILE READER — extract headers + sample rows from any format
# ──────────────────────────────────────────────────────────

def _read_file_sample(file_path: str) -> tuple[list, str]:
    """
    Returns (headers, sample_rows_str) from a structured or unstructured file.
    For PDFs / plain text, headers = [] and sample_rows_str = first ~2000 chars.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    headers = []
    sample = ""

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path, nrows=5)
            headers = list(df.columns)
            sample = df.to_csv(index=False)

        elif ext == ".tsv":
            df = pd.read_csv(file_path, sep="\t", nrows=5)
            headers = list(df.columns)
            sample = df.to_csv(index=False, sep="\t")

        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, nrows=5)
            headers = list(df.columns)
            sample = df.to_string(index=False)

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                headers = list(data[0].keys())
                sample = json.dumps(data[:5], indent=2)
            elif isinstance(data, dict):
                headers = list(data.keys())
                sample = json.dumps(data, indent=2)[:2000]

        elif ext == ".pdf":
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = "\n".join(p.extract_text() or "" for p in reader.pages[:3])
            headers = []
            sample = text[:2000]

        else:
            # Plain text fallback
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                sample = f.read(2000)
            headers = []

    except Exception as e:
        print(f"[SchemaAnalyzer] Error reading {file_path}: {e}")
        sample = f"[read error: {e}]"

    return headers, sample


# ──────────────────────────────────────────────────────────
# HEURISTIC CLASSIFIER — offline fallback
# ──────────────────────────────────────────────────────────

def _heuristic_analyze(filename: str, headers: list, sample_text: str) -> dict:
    """
    Keyword-based structural classifier used when Gemini is unavailable.
    Returns the same shape as the LLM response.
    """
    hl = [h.lower() for h in headers]
    combined_text = " ".join(hl) + " " + filename.lower() + " " + sample_text.lower()

    scores = {
        "CDR": 0,
        "BANK_TRANSACTION": 0,
        "GPS": 0,
        "CHAT_LOG": 0,
        "EMAIL": 0,
        "FIR": 0,
    }

    # CDR signals
    for kw in ["caller", "receiver", "call", "mobile", "phone", "duration", "tower", "cell"]:
        if kw in combined_text:
            scores["CDR"] += 1

    # BANK signals
    for kw in ["sender_acc", "receiver_acc", "account", "amount", "transfer", "debit",
                "credit", "bank", "txn", "transaction", "ifsc", "wire"]:
        if kw in combined_text:
            scores["BANK_TRANSACTION"] += 1

    # GPS signals
    for kw in ["latitude", "longitude", "lat", "lon", "gps", "device", "speed",
                "accuracy", "tracker", "vehicle", "location_fix"]:
        if kw in combined_text:
            scores["GPS"] += 1

    # CHAT / EMAIL signals
    for kw in ["message", "chat", "whatsapp", "telegram", "sender", "receiver"]:
        if kw in combined_text:
            scores["CHAT_LOG"] += 1

    for kw in ["from:", "to:", "subject", "email", "reply", "cc:", "bcc:"]:
        if kw in combined_text:
            scores["EMAIL"] += 1

    # FIR signals (must dominate for unstructured)
    for kw in ["fir", "complaint", "police", "accused", "offence", "incident",
                "charges", "ipc", "complainant", "first information"]:
        if kw in combined_text:
            scores["FIR"] += 2  # weighted higher for unstructured

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return {"dataset_type": "UNKNOWN", "column_mapping": {}, "confidence": 0.0, "mode": "heuristic"}

    confidence = min(0.90, 0.50 + best_score * 0.08)

    # Build mapping for structured types
    mapping = {}
    if best_type == "CDR":
        for h in headers:
            hl_h = h.lower()
            if any(k in hl_h for k in ["caller", "from_mob", "src", "from", "source"]) and "caller_number" not in mapping:
                mapping["caller_number"] = h
            elif any(k in hl_h for k in ["receiver", "to_mob", "dst", "destination", "to"]) and "receiver_number" not in mapping:
                mapping["receiver_number"] = h
            elif any(k in hl_h for k in ["time", "date", "timestamp"]) and "timestamp" not in mapping:
                mapping["timestamp"] = h
            elif any(k in hl_h for k in ["duration", "sec", "length"]) and "duration" not in mapping:
                mapping["duration"] = h
            elif any(k in hl_h for k in ["tower", "cell", "code"]) and "tower_id" not in mapping:
                mapping["tower_id"] = h

    elif best_type == "BANK_TRANSACTION":
        for h in headers:
            hl_h = h.lower()
            if any(k in hl_h for k in ["sender", "from_acc", "source_acc", "from", "source"]) and "sender_acc" not in mapping:
                mapping["sender_acc"] = h
            elif any(k in hl_h for k in ["receiver", "to_acc", "dest_acc", "destination", "to"]) and "receiver_acc" not in mapping:
                mapping["receiver_acc"] = h
            elif any(k in hl_h for k in ["amount", "val", "value", "transfer_val", "sum"]) and "amount" not in mapping:
                mapping["amount"] = h
            elif any(k in hl_h for k in ["time", "date", "tx_date", "timestamp"]) and "timestamp" not in mapping:
                mapping["timestamp"] = h
            elif any(k in hl_h for k in ["type", "method", "mode"]) and "txn_type" not in mapping:
                mapping["txn_type"] = h

    elif best_type == "GPS":
        for h in headers:
            hl_h = h.lower()
            if any(k in hl_h for k in ["device", "phone", "vehicle", "id", "tracker"]) and "device_id" not in mapping:
                mapping["device_id"] = h
            elif "lat" in hl_h and "latitude" not in mapping:
                mapping["latitude"] = h
            elif any(k in hl_h for k in ["lon", "lng"]) and "longitude" not in mapping:
                mapping["longitude"] = h
            elif any(k in hl_h for k in ["time", "date", "timestamp"]) and "timestamp" not in mapping:
                mapping["timestamp"] = h
            elif "speed" in hl_h and "speed" not in mapping:
                mapping["speed"] = h
            elif "accuracy" in hl_h and "accuracy" not in mapping:
                mapping["accuracy"] = h

    return {
        "dataset_type": best_type,
        "column_mapping": mapping,
        "confidence": confidence,
        "mode": "heuristic",
    }


# ──────────────────────────────────────────────────────────
# LLM ANALYZER
# ──────────────────────────────────────────────────────────

def _llm_analyze(filename: str, extension: str, headers: list, sample_text: str) -> dict | None:
    """
    Query Gemini 2.5 Flash to classify and map the schema.
    Returns None on failure (caller should fall back to heuristic).
    """
    genai = _get_genai()
    if genai is None:
        return None

    prompt = _PROMPT_TEMPLATE.format(
        filename=filename,
        extension=extension,
        headers=headers if headers else "(no structured headers — unstructured file)",
        sample_rows=sample_text[:2500],
    )

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        result = json.loads(response.text)
        result["mode"] = "llm"
        return result
    except Exception as e:
        print(f"[SchemaAnalyzer] Gemini call failed: {e}")
        return None


# ──────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────

def analyze(file_path: str) -> dict:
    """
    Main entry point.

    Reads the file, calls Gemini (or heuristic fallback), and returns:

    {
        "dataset_type": "CDR",
        "column_mapping": {
            "caller_number": "source",
            "receiver_number": "destination",
            ...
        },
        "confidence": 0.95,
        "mode": "llm" | "heuristic"
    }

    Raises ValueError if confidence is below CONFIDENCE_THRESHOLD.
    """
    path = Path(file_path)
    filename = path.name
    extension = path.suffix.lower()

    print(f"[SchemaAnalyzer] Analyzing: {filename}")

    headers, sample_text = _read_file_sample(file_path)

    # Try LLM first
    result = _llm_analyze(filename, extension, headers, sample_text)

    # Fall back to heuristic if LLM unavailable or failed
    if result is None:
        print(f"[SchemaAnalyzer] Falling back to heuristic classifier for: {filename}")
        result = _heuristic_analyze(filename, headers, sample_text)
    else:
        print(f"[SchemaAnalyzer] Gemini classified as: {result.get('dataset_type')} "
              f"(confidence={result.get('confidence')})")

    dataset_type = result.get("dataset_type", "UNKNOWN")
    confidence = float(result.get("confidence", 0.0))

    if confidence < CONFIDENCE_THRESHOLD and dataset_type not in ("FIR", "CASE_NOTES"):
        raise ValueError(
            f"[SchemaAnalyzer] Confidence {confidence:.2f} is below threshold "
            f"{CONFIDENCE_THRESHOLD} for '{filename}'. "
            f"Detected type: {dataset_type}. Cannot proceed — schema unclear."
        )

    return result
