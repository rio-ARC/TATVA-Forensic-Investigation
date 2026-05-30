# Go up one level, then into preprocessor/folder
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Now import your function
from preprocessor.FIR_Preprocessed.fir           import preprocess_fir
from preprocessor.CallDetailsRecord.cdr          import preprocess_cdr
from preprocessor.GPS_Preprocessed.gps           import preprocess_gps
from preprocessor.Chats_Social.main              import preprocess_socials
from preprocessor.bank_transaction_pipeline.main import preprocess_transaction

# ------------------------------------------------
# DATA DIRECTORY
# ------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"

# ------------------------------------------------
# LOAD RAW INPUT FILES
# ------------------------------------------------

FIR_FILE = DATA_DIR / "fir.txt"

CDR_FILE = DATA_DIR / "cdr.csv"

GPS_FILE = DATA_DIR / "gps.csv"

SOCIAL_FILES = [
    DATA_DIR / "emails.txt",
    DATA_DIR / "chat.txt",
    DATA_DIR / "social.json"
]

BANK_FILE = DATA_DIR / "transactions.csv"

VEHICLE_DATA_DIR = Path(__file__).parent.parent / "preprocessor" / "Vehicle_License_preprocessed"

# ------------------------------------------------
# RUN PREPROCESSORS
# ------------------------------------------------

def run_all_preprocessors():

    all_graphs = []

    # ------------------------------------------------
    # FIR PREPROCESSING
    # ------------------------------------------------

    try:
        with open(FIR_FILE, "r", encoding="utf-8") as f:
            fir_text = f.read()

        fir_graph = preprocess_fir(fir_text)
        print("[OK] FIR preprocessing completed")
        all_graphs.append(fir_graph)

    except Exception as e:
        print(f"[FAIL] FIR preprocessing failed: {e}")

    # ------------------------------------------------
    # CDR PREPROCESSING
    # ------------------------------------------------

    try:
        cdr_graph = preprocess_cdr(str(CDR_FILE))
        print("[OK] CDR preprocessing completed")
        all_graphs.append(cdr_graph)

    except Exception as e:
        print(f"[FAIL] CDR preprocessing failed: {e}")

    # ------------------------------------------------
    # GPS PREPROCESSING
    # ------------------------------------------------

    try:
        gps_graph = preprocess_gps(str(GPS_FILE))
        print("[OK] GPS preprocessing completed")
        all_graphs.append(gps_graph)

    except Exception as e:
        print(f"[FAIL] GPS preprocessing failed: {e}")

    # ------------------------------------------------
    # SOCIAL / CHAT PREPROCESSING
    # ------------------------------------------------

    try:
        social_graph = preprocess_socials(
            [str(file_path) for file_path in SOCIAL_FILES]
        )
        print("[OK] Social preprocessing completed")
        all_graphs.append(social_graph)

    except Exception as e:
        print(f"[FAIL] Social preprocessing failed: {e}")

    # ------------------------------------------------
    # BANK TRANSACTION PREPROCESSING
    # ------------------------------------------------

    try:
        bank_graph = preprocess_transaction(str(BANK_FILE), save_intermediates=False)
        print("[OK] Bank preprocessing completed")
        all_graphs.append(bank_graph)

    except Exception as e:
        print(f"[FAIL] Bank preprocessing failed: {e}")

    # ------------------------------------------------
    # VEHICLE LICENSE PREPROCESSING
    # ------------------------------------------------

    try:
        from preprocessor.Vehicle_License_preprocessed.vehicle import preprocess_vehicle
        vehicle_graph = preprocess_vehicle(str(VEHICLE_DATA_DIR))
        print("[OK] Vehicle preprocessing completed")
        all_graphs.append(vehicle_graph)

    except Exception as e:
        print(f"[FAIL] Vehicle preprocessing failed: {e}")

    return all_graphs

# ------------------------------------------------
# MERGE ALL ENTITIES + RELATIONS
# ------------------------------------------------

def collect_graph_components(all_graphs):

    all_entities = []
    all_relations = []

    for graph in all_graphs:

        entities = graph.get("entities", [])
        relations = graph.get("relations", [])
        all_entities.extend(entities)
        all_relations.extend(relations)

    return {
        "entities": all_entities,
        "relations": all_relations
    }

# ------------------------------------------------
# SAVE OUTPUT
# ------------------------------------------------

def save_preprocessed_output(output_data):

    output_path = (Path(__file__).parent/ "output" / "all_preprocessed_graphs.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print(f"[OK] Saved combined graph data to: {output_path}")

# ------------------------------------------------
# MAIN
# ------------------------------------------------

if __name__ == "__main__":

    print("\n========== RUNNING PREPROCESSORS ==========\n")

    all_graphs = run_all_preprocessors()

    print(f"\n[INFO] Total preprocessors executed: {len(all_graphs)}")

    combined_graph = collect_graph_components(all_graphs)

    print(
        f"[INFO] Total entities collected: "
        f"{len(combined_graph['entities'])}"
    )

    print(
        f"[INFO] Total relations collected: "
        f"{len(combined_graph['relations'])}"
    )

    save_preprocessed_output(combined_graph)

    print("\n========== PREPROCESSING COMPLETE ==========\n")

