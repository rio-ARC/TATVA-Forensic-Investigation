# main.py

import json
import sys
from pathlib import Path

# Ensure imports work regardless of where this script is called from
sys.path.insert(0, str(Path(__file__).parent))

from preprocessed_outputs import (run_all_preprocessors, collect_graph_components)
from entity_resolution import (resolve_entities)
from graph_integrator import (integrate_graph, save_unified_graph)
from investigator_annotations import (load_annotations, build_annotation_relations)

# ------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------

def main():

    print("\n========== STEP 1 ==========")
    print("RUNNING PREPROCESSORS\n")

    all_graphs = run_all_preprocessors()

    combined_graph = (collect_graph_components(all_graphs))

    entities = combined_graph["entities"]

    relations = combined_graph["relations"]

    print(f"[INFO] Entities: {len(entities)}")

    print(f"[INFO] Relations: {len(relations)}")

    # ------------------------------------------------
    # BUILD ENTITY LOOKUP
    # ------------------------------------------------

    entity_lookup = {}

    for entity in entities:

        entity_id = (
            entity.get("temp_id")
            or entity.get("id")
        )

        entity_lookup[entity_id] = entity

    # ------------------------------------------------
    # LOAD INVESTIGATOR ANNOTATIONS
    # ------------------------------------------------

    print("\n========== STEP 2 ==========")
    print("LOADING INVESTIGATOR ANNOTATIONS\n")

    annotations = load_annotations(str(Path(__file__).parent / "data" / "annotations.csv"))

    annotation_relations = (build_annotation_relations(annotations, entity_lookup))

    relations.extend(annotation_relations)

    print(
        f"[INFO] Annotation Relations: "
        f"{len(annotation_relations)}"
    )

    print(
        f"[INFO] Updated Relations: "
        f"{len(relations)}"
    )

    # ------------------------------------------------
    # ENTITY RESOLUTION
    # ------------------------------------------------

    print("\n========== STEP 3 ==========")
    print("ENTITY RESOLUTION\n")

    resolution_output = resolve_entities(
        entities,
        relations
    )

    print(
        f"[INFO] Master Entities: "
        f"{len(resolution_output['master_entities'])}"
    )

    # ------------------------------------------------
    # GRAPH INTEGRATION
    # ------------------------------------------------

    print("\n========== STEP 4 ==========")
    print("GRAPH INTEGRATION\n")

    unified_graph = integrate_graph(
        entities,
        relations,
        resolution_output
    )

    print(
        f"[INFO] Final Relations: "
        f"{len(unified_graph['relations'])}"
    )

    # ------------------------------------------------
    # SAVE
    # ------------------------------------------------

    save_unified_graph(
        unified_graph,
        str(Path(__file__).parent / "output" / "unified_graph.json")
    )

    print(
        "\n========== COMPLETE ==========\n"
    )


# ------------------------------------------------
# RUN
# ------------------------------------------------

if __name__ == "__main__":

    main()
