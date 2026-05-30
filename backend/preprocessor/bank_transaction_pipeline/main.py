from .preprocessing.cleaner import clean_transactions
from .preprocessing.feature_engineering import generate_features
from .preprocessing.anomaly_detection import detect_suspicious_transactions, save_suspicious_transactions
from .preprocessing.graph_builder import build_graph, save_graph

import json
import os

RAW_DATA = "data/raw/transactions.csv"

CLEANED_DATA = "data/processed/cleaned_transactions.csv"

SUSPICIOUS_OUTPUT = "data/processed/suspicious_transactions.json"

NODE_OUTPUT = "data/processed/nodes.json"

EDGE_OUTPUT = "data/processed/edges.json"


def preprocess_transaction(raw_data_path, base_directory=".", save_intermediates=True, mapping=None):
    """
    Preprocess bank transactions and return graph data as JSON.
    
    Args:
        raw_data_path (str):    Path to the raw transactions CSV file.
        base_directory (str):   Base directory for saving processed files.
        save_intermediates (bool): Whether to save intermediate processing files.
        mapping (dict|None):    Optional {canonical_col: raw_col} from SchemaAnalyzer.
                                When provided, arbitrary column names are remapped to
                                canonical names before processing.
    
    Returns:
        dict: JSON structure with 'entities' and 'relations' keys.
    """
    
    # Build output paths based on base_directory
    processed_dir = os.path.join(base_directory, "data", "processed")
    cleaned_data_path = os.path.join(processed_dir, "cleaned_transactions.csv")
    suspicious_output_path = os.path.join(processed_dir, "suspicious_transactions.json")
    nodes_output_path = os.path.join(processed_dir, "nodes.json")
    edges_output_path = os.path.join(processed_dir, "edges.json")
    
    # Create output directory if saving intermediates
    if save_intermediates:
        os.makedirs(processed_dir, exist_ok=True)

    print("Cleaning transaction data...")
    if save_intermediates:
        df = clean_transactions(raw_data_path, cleaned_data_path, mapping=mapping)
    else:
        df = clean_transactions(raw_data_path, None, mapping=mapping)

    print("Generating features...")
    features = generate_features(df)

    print("Detecting anomalies...")
    suspicious = detect_suspicious_transactions(df)

    if save_intermediates:
        print("Saving suspicious transaction report...")
        save_suspicious_transactions(suspicious, suspicious_output_path)

    print("Building graph...")
    nodes, edges = build_graph(df, features, suspicious)

    if save_intermediates:
        print("Saving graph JSON...")
        save_graph(nodes, edges, nodes_output_path, edges_output_path)

    print("Pipeline completed successfully!")

    return {
        "entities": nodes,
        "relations": edges
    }


if __name__ == "__main__":
    # For testing with default path
    result = preprocess_transaction(
        raw_data_path=RAW_DATA,
        base_directory=".",
        save_intermediates=True
    )
    print("\nReturned Graph Data:")
    print(json.dumps(result, indent=2, default=str))