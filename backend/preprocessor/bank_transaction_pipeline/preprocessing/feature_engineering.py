# Feature engineering for bank transaction data

# basically, we will group transactions by sender account and create features like:
# - transaction frequency   
# - average transaction amount
# - ratio of night transactions (e.g. between 12 AM and 4 AM)
# - number of unique receivers


# We are considering account as sender_acc for feature generation and group is that dataframe of transactions for that sender account. We are calculating the features based on the transactions made by that sender account.

import pandas as pd

def generate_features(df):

    feature_dict = {}

    grouped = df.groupby("sender_acc")

    for account, group in grouped:

        txn_frequency = len(group)

        avg_amount = group["amount"].mean()

        night_txn_ratio = len(
            group[
                (group["timestamp"].dt.hour >= 0) &
                (group["timestamp"].dt.hour <= 4)
            ]
        ) / txn_frequency

        unique_receivers = group["receiver_acc"].nunique()

        feature_dict[account] = {
            "txn_frequency": txn_frequency,
            "avg_amount": avg_amount,
            "night_txn_ratio": round(night_txn_ratio, 2),
            "unique_receivers": unique_receivers
        }

    return feature_dict

if __name__ == "__main__":
    # Example usage
    df = pd.read_csv("data/raw/repetitive_sender_transactions.csv", parse_dates=["timestamp"])
    features = generate_features(df)
    for account, feats in features.items():
        print(f"Account: {account}")
        for feat_name, feat_value in feats.items():
            print(f"  {feat_name}: {feat_value}")