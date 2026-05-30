import pandas as pd

def clean_transactions(input_path, output_path, mapping=None):
    """
    Clean and normalize a raw bank transaction file.

    Args:
        input_path:  Path to the raw CSV file.
        output_path: Path to write cleaned file (None = skip writing).
        mapping:     Optional {canonical_col: raw_col} dict from SchemaAnalyzer.
                     When provided, raw column names are renamed to canonical names.
                     When None, canonical column names are assumed directly.

    Returns:
        Cleaned DataFrame with canonical column names.
    """

    df = pd.read_csv(input_path)

    # ── Apply column mapping if provided ──────────────────────
    if mapping:
        rename_map = {
            raw_col: canonical_col
            for canonical_col, raw_col in mapping.items()
            if raw_col in df.columns
        }
        df = df.rename(columns=rename_map)

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove negative amounts
    df["amount"] = df["amount"].abs()

    # Normalize timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Remove rows with missing important fields
    df = df.dropna(subset=[
        "sender_acc",
        "receiver_acc",
        "amount",
        "timestamp"
    ])

    # Standardize account IDs
    df["sender_acc"] = df["sender_acc"].str.upper()
    df["receiver_acc"] = df["receiver_acc"].str.upper()

    # Fill optional columns with defaults if absent
    if "txn_type" not in df.columns:
        df["txn_type"] = "TRANSFER"
    if "location" not in df.columns:
        df["location"] = "Unknown"

    if output_path:
        df.to_csv(output_path, index=False)

    return df