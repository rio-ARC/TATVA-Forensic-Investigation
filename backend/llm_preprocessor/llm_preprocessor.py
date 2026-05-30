"""
llm_preprocessor/llm_preprocessor.py
======================================
Top-level orchestrator for the TATVA Data Understanding Layer.

Flow:
  Upload
    ↓
  SchemaAnalyzer          — LLM (Gemini 2.5 Flash) or Heuristic fallback
    ↓                         Outputs: dataset_type, column_mapping, confidence
  Structured?
  ├─ Yes -> SchemaMapper   — Renames raw columns to canonical names (pure pandas)
  │           ↓
  │         Router        — Calls the right deterministic preprocessor with mapping
  │           ↓
  │         Graph output  — {"entities": [...], "relations": [...]}
  └─ No  -> UnstructuredHandler
              ↓              — Extracts text (PDF/TXT) -> spacy / existing FIR pipeline
            Graph output

No downstream interface changes.
Entity Resolution, Graph Integration, Timeline Reconstruction, Risk Scoring,
and Neo4j ingestion remain unaffected.
"""

import sys
from pathlib import Path

# Ensure backend root is importable
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from .schema_analyzer import analyze
from .canonical_schemas import STRUCTURED_TYPES, UNSTRUCTURED_TYPES

# ──────────────────────────────────────────────────────────
# STRUCTURED ROUTER
# ──────────────────────────────────────────────────────────

def _route_structured(file_path: str, dataset_type: str, column_mapping: dict) -> dict:
    """
    Route a structured file through the correct deterministic preprocessor,
    passing the column_mapping so the preprocessor can resolve raw column names.
    """

    if dataset_type == "CDR":
        from preprocessor.CallDetailsRecord.cdr import preprocess_cdr
        print(f"[Router] -> CDRPreprocessor  (mapping={column_mapping})")
        return preprocess_cdr(file_path, mapping=column_mapping)

    elif dataset_type == "BANK_TRANSACTION":
        from preprocessor.bank_transaction_pipeline.main import preprocess_transaction
        print(f"[Router] -> BankTransactionPreprocessor  (mapping={column_mapping})")
        return preprocess_transaction(file_path, save_intermediates=False, mapping=column_mapping)

    elif dataset_type == "GPS":
        from preprocessor.GPS_Preprocessed.gps import preprocess_gps
        print(f"[Router] -> GPSPreprocessor  (mapping={column_mapping})")
        return preprocess_gps(file_path, mapping=column_mapping)

    elif dataset_type in ("CHAT_LOG", "EMAIL"):
        from preprocessor.Chats_Social.main import preprocess_socials
        print(f"[Router] -> SocialPreprocessor  (type={dataset_type})")
        return preprocess_socials([file_path])

    else:
        raise ValueError(
            f"[Router] No deterministic preprocessor registered for type '{dataset_type}'."
        )


# ──────────────────────────────────────────────────────────
# UNSTRUCTURED HANDLER
# ──────────────────────────────────────────────────────────

def _handle_unstructured(file_path: str, dataset_type: str) -> dict:
    """
    Handle unstructured files (PDF, TXT, FIR reports, case notes).
    Extracts raw text and routes to the spacy NLP preprocessor.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    raw_text = ""

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            raw_text = "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            raise RuntimeError(f"[UnstructuredHandler] Failed to read PDF '{file_path}': {e}")

    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

    if dataset_type in ("FIR", "CASE_NOTES", "REPORT"):
        from preprocessor.FIR_Preprocessed.fir import preprocess_fir
        print(f"[Router] -> FIRPreprocessor  (type={dataset_type})")
        return preprocess_fir(raw_text)

    # Generic fallback for unknown unstructured
    print(f"[Router] Unknown unstructured type '{dataset_type}' — using FIR pipeline as fallback.")
    from preprocessor.FIR_Preprocessed.fir import preprocess_fir
    return preprocess_fir(raw_text)


# ──────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────

def process_file(file_path: str) -> dict:
    """
    Main entry point.

    Accepts any evidence file (CSV, XLSX, JSON, TSV, PDF, TXT).
    Returns the standard graph output contract:

        {
            "dataset_type": "CDR",
            "confidence": 0.95,
            "mode": "llm" | "heuristic",
            "graph": {
                "entities": [...],
                "relations": [...]
            }
        }

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the schema cannot be determined with sufficient confidence.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"[LLMPreprocessor] File not found: {file_path}")

    # Step 1 — Schema Analysis
    analysis = analyze(file_path)
    dataset_type  = analysis["dataset_type"].upper()
    column_mapping = analysis.get("column_mapping", {})
    confidence    = analysis.get("confidence", 0.0)
    mode          = analysis.get("mode", "unknown")

    print(f"[LLMPreprocessor] '{path.name}' -> type={dataset_type}  confidence={confidence:.2f}  mode={mode}")

    # Step 2 — Route to correct pipeline
    if dataset_type in STRUCTURED_TYPES:
        graph = _route_structured(file_path, dataset_type, column_mapping)
    else:
        graph = _handle_unstructured(file_path, dataset_type)

    return {
        "dataset_type": dataset_type,
        "confidence": confidence,
        "mode": mode,
        "graph": graph,
    }


# ──────────────────────────────────────────────────────────
# CONVENIENCE CLASS (thin wrapper — keeps old import paths working)
# ──────────────────────────────────────────────────────────

class LLMPreprocessor:
    """
    Thin class wrapper around process_file().
    Keeps any external code that instantiated LLMPreprocessor() working.
    """
    def preprocess_raw_file(self, raw_file_path: str, **kwargs) -> dict:
        return process_file(raw_file_path)

    def classify_and_map_file(self, file_path: str) -> dict:
        """Expose just the schema analysis step."""
        return analyze(file_path)


# ──────────────────────────────────────────────────────────
# TEST RUNNER
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("\n========== TESTING TATVA DATA UNDERSTANDING LAYER ==========\n")

    sample_dir = Path(__file__).parent / "samples"

    test_files = [
        ("CDR (non-standard headers)",  sample_dir / "sample_1.csv"),
        ("BANK (non-standard headers)", sample_dir / "sample_2.csv"),
        ("FIR PDF",                     sample_dir / "sample_fir.pdf"),
    ]

    for label, fpath in test_files:
        if not fpath.exists():
            print(f"[SKIP] {label}: file not found at {fpath}")
            continue

        print(f"\n{'='*60}")
        print(f"  Testing: {label}")
        print(f"{'='*60}")
        try:
            result = process_file(str(fpath))
            graph  = result["graph"]
            print(f"  [SUCCESS] dataset_type = {result['dataset_type']}")
            print(f"            confidence   = {result['confidence']:.2f}")
            print(f"            mode         = {result['mode']}")
            print(f"            entities     = {len(graph['entities'])}")
            print(f"            relations    = {len(graph['relations'])}")
            if graph["entities"]:
                print("  First entity:")
                print("  " + json.dumps(graph["entities"][0], indent=4).replace("\n", "\n  "))
        except Exception as e:
            print(f"  [FAIL] {e}")

    print("\n========== TEST COMPLETE ==========\n")
