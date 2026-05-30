import pandas as pd

def clean_transactions(input_path, output_path):

    df = pd.read_csv(input_path)

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

    df.to_csv(output_path, index=False)

    return df