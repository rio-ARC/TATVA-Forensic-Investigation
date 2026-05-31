# Graph_Integration_Layer/main.py
# ================================
# Orchestrator for the TATVA Graph Integration Pipeline.
#
# Two modes:
#   1. DYNAMIC (case_id provided):
#      - Scans uploads/{case_id}/ for uploaded evidence files.
#      - Routes each file through llm_preprocessor.process_file() which:
#          a) Runs LLM schema analysis (Gemini or heuristic fallback)
#          b) Maps raw columns to canonical schema
#          c) Calls the correct deterministic preprocessor
#      - Merges all entity/relation subgraphs.
#      - Loads investigator annotations from uploads (or falls back to data/).
#      - Runs Entity Resolution → Graph Integration → Save unified_graph.json.
#
#   2. STATIC / LEGACY (case_id=None):
#      - Falls back to the original hardcoded preprocessed_outputs.py pipeline.
#      - Guarantees backward-compatible standalone usage.

import json
import sys
from pathlib import Path

# Ensure imports work regardless of call site
_GIL_DIR = Path(__file__).parent
_BACKEND_DIR = _GIL_DIR.parent
sys.path.insert(0, str(_GIL_DIR))
sys.path.insert(0, str(_BACKEND_DIR))

from entity_resolution import resolve_entities
from graph_integrator import integrate_graph, save_unified_graph
from investigator_annotations import load_annotations, build_annotation_relations


# ---------------------------------------------------------------------------
# DYNAMIC PATH — invoked when a case_id is available
# ---------------------------------------------------------------------------

def _run_dynamic_pipeline(case_id: str) -> None:
    """
    Scan uploads/{case_id}/, route each file through the LLM preprocessor,
    merge results, resolve entities, integrate, and save unified_graph.json.
    """
    from llm_preprocessor.llm_preprocessor import process_file

    uploads_dir = _BACKEND_DIR / "uploads" / case_id
    output_path = _GIL_DIR / "output" / "unified_graph.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not uploads_dir.exists():
        print(f"[GIL] WARNING: Upload directory '{uploads_dir}' not found. Falling back to static pipeline.")
        _run_static_pipeline()
        return

    # ── Scan uploaded files ──────────────────────────────────────────────────
    all_files = [f for f in uploads_dir.iterdir() if f.is_file()]
    if not all_files:
        print(f"[GIL] WARNING: No uploaded files found in '{uploads_dir}'. Falling back to static pipeline.")
        _run_static_pipeline()
        return

    print(f"\n========== STEP 1 ==========")
    print(f"SCANNING UPLOADS FOR CASE: {case_id}")
    print(f"Found {len(all_files)} file(s): {[f.name for f in all_files]}\n")

    # Separate annotation files from evidence files
    annotation_file: Path | None = None
    evidence_files: list[Path] = []

    for f in all_files:
        if "annotation" in f.name.lower():
            annotation_file = f
            print(f"  [ANNOTATION] {f.name} -> will use as investigator annotations")
        else:
            evidence_files.append(f)
            print(f"  [EVIDENCE]   {f.name} -> will route through LLM preprocessor")

    # ── Route each evidence file through the LLM preprocessor ───────────────
    all_graphs: list[dict] = []

    print(f"\n========== STEP 2 ==========")
    print("LLM SCHEMA ANALYSIS & DETERMINISTIC PREPROCESSING\n")

    for evidence_file in evidence_files:
        file_str = str(evidence_file)
        try:
            result = process_file(file_str)
            graph = result.get("graph", {})
            entities = graph.get("entities", [])
            relations = graph.get("relations", [])
            print(
                f"  [OK] {evidence_file.name} -> "
                f"type={result['dataset_type']}  "
                f"conf={result['confidence']:.2f}  "
                f"mode={result['mode']}  "
                f"entities={len(entities)}  relations={len(relations)}"
            )
            all_graphs.append(graph)
        except ValueError as ve:
            # Schema confidence below threshold — for .txt/.json unstructured files,
            # fall back to the FIR/unstructured pipeline rather than dropping the file.
            ext = evidence_file.suffix.lower()
            if ext in (".txt", ".json", ".pdf"):
                print(f"  [FALLBACK] {evidence_file.name} -> schema unclear, routing as unstructured FIR...")
                try:
                    from preprocessor.FIR_Preprocessed.fir import preprocess_fir
                    with open(file_str, "r", encoding="utf-8", errors="ignore") as fh:
                        raw_text = fh.read()
                    fallback_graph = preprocess_fir(raw_text)
                    entities = fallback_graph.get("entities", [])
                    relations = fallback_graph.get("relations", [])
                    print(f"  [OK-FALLBACK] {evidence_file.name} -> type=FIR  entities={len(entities)}  relations={len(relations)}")
                    all_graphs.append(fallback_graph)
                except Exception as fe:
                    print(f"  [FAIL] {evidence_file.name} -> FIR fallback also failed: {fe}")
            else:
                print(f"  [SKIP] {evidence_file.name} -> {ve}")
        except Exception as e:
            print(f"  [FAIL] {evidence_file.name} -> {e}")

    # ── Collect all entities and relations ───────────────────────────────────
    print(f"\n========== STEP 3 ==========")
    print("MERGING ENTITY & RELATION GRAPHS\n")

    all_entities: list[dict] = []
    all_relations: list[dict] = []

    for g in all_graphs:
        all_entities.extend(g.get("entities", []))
        all_relations.extend(g.get("relations", []))

    print(f"[INFO] Merged Entities:  {len(all_entities)}")
    print(f"[INFO] Merged Relations: {len(all_relations)}")

    # ── Build entity lookup ──────────────────────────────────────────────────
    entity_lookup: dict = {}
    for entity in all_entities:
        eid = entity.get("temp_id") or entity.get("id")
        if eid:
            entity_lookup[eid] = entity

    # ── Load investigator annotations ────────────────────────────────────────
    print(f"\n========== STEP 4 ==========")
    print("LOADING INVESTIGATOR ANNOTATIONS\n")

    # Prefer the uploaded annotation file; fall back to bundled data/annotations.csv
    annotation_path = str(annotation_file) if annotation_file else str(_GIL_DIR / "data" / "annotations.csv")
    print(f"  Using annotation source: {annotation_path}")

    try:
        annotations = load_annotations(annotation_path)
        annotation_relations = build_annotation_relations(annotations, entity_lookup)
        all_relations.extend(annotation_relations)
        print(f"  [OK] Annotation Relations loaded: {len(annotation_relations)}")
    except Exception as e:
        print(f"  [WARN] Could not load annotations: {e}")

    print(f"[INFO] Total Relations (incl. annotations): {len(all_relations)}")

    # ── Entity Resolution ────────────────────────────────────────────────────
    print(f"\n========== STEP 5 ==========")
    print("ENTITY RESOLUTION\n")

    resolution_output = resolve_entities(all_entities, all_relations)
    print(f"[INFO] Master Entities: {len(resolution_output['master_entities'])}")

    # ── Graph Integration ────────────────────────────────────────────────────
    print(f"\n========== STEP 6 ==========")
    print("GRAPH INTEGRATION\n")

    unified_graph = integrate_graph(all_entities, all_relations, resolution_output)
    print(f"[INFO] Final Relations in Unified Graph: {len(unified_graph['relations'])}")

    # ── Save ─────────────────────────────────────────────────────────────────
    save_unified_graph(unified_graph, str(output_path))
    print(f"\n========== COMPLETE ==========")
    print(f"[GIL] Saved unified_graph.json -> {output_path}\n")


# ---------------------------------------------------------------------------
# STATIC / LEGACY PATH — used when no case_id is given
# ---------------------------------------------------------------------------

def _run_static_pipeline() -> None:
    """
    Original hardcoded pipeline using preprocessed_outputs.py.
    Kept for backward-compatible standalone runs and testing.
    """
    from preprocessed_outputs import run_all_preprocessors, collect_graph_components

    print(f"\n========== STEP 1 ==========")
    print("RUNNING STATIC PREPROCESSORS (legacy mode)\n")

    all_graphs = run_all_preprocessors()
    combined_graph = collect_graph_components(all_graphs)
    entities = combined_graph["entities"]
    relations = combined_graph["relations"]

    print(f"[INFO] Entities:  {len(entities)}")
    print(f"[INFO] Relations: {len(relations)}")

    entity_lookup: dict = {}
    for entity in entities:
        eid = entity.get("temp_id") or entity.get("id")
        if eid:
            entity_lookup[eid] = entity

    print(f"\n========== STEP 2 ==========")
    print("LOADING INVESTIGATOR ANNOTATIONS\n")

    annotations = load_annotations(str(_GIL_DIR / "data" / "annotations.csv"))
    annotation_relations = build_annotation_relations(annotations, entity_lookup)
    relations.extend(annotation_relations)
    print(f"[INFO] Annotation Relations: {len(annotation_relations)}")
    print(f"[INFO] Updated Relations:    {len(relations)}")

    print(f"\n========== STEP 3 ==========")
    print("ENTITY RESOLUTION\n")

    resolution_output = resolve_entities(entities, relations)
    print(f"[INFO] Master Entities: {len(resolution_output['master_entities'])}")

    print(f"\n========== STEP 4 ==========")
    print("GRAPH INTEGRATION\n")

    unified_graph = integrate_graph(entities, relations, resolution_output)
    print(f"[INFO] Final Relations: {len(unified_graph['relations'])}")

    save_unified_graph(
        unified_graph,
        str(_GIL_DIR / "output" / "unified_graph.json")
    )
    print(f"\n========== COMPLETE ==========\n")


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def main(case_id: str | None = None) -> None:
    """
    Main entry point for the Graph Integration Layer.

    Args:
        case_id: If provided, scans uploads/{case_id}/ and runs the dynamic
                 LLM-routed pipeline. If None, falls back to the static
                 legacy pipeline (backward compatible).
    """
    if case_id:
        print(f"[GIL] Starting DYNAMIC pipeline for case: {case_id}")
        _run_dynamic_pipeline(case_id)
    else:
        print("[GIL] Starting STATIC (legacy) pipeline.")
        _run_static_pipeline()


# ---------------------------------------------------------------------------
# STANDALONE RUN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TATVA Graph Integration Layer")
    parser.add_argument("--case-id", type=str, default=None,
                        help="Case ID to process from uploads/ directory. Omit for legacy static mode.")
    args = parser.parse_args()
    main(case_id=args.case_id)
