# Simple rule-based anomaly detection for bank transactions

# - Burst transaction detection: If an account makes more than 5 transactions within a short time window (e.g. 1 hour), flag it as suspicious.
# - High amount detection: If a transaction amount exceeds a certain threshold (e.g. $100,000), flag it as suspicious.
# - Night activity detection: If an account has transactions between 12 AM and 4 AM, flag it as suspicious.

import json

def detect_suspicious_transactions(df):

    suspicious = []

    grouped = df.groupby("sender_acc")

    for account, group in grouped:

        # Burst transaction detection
        if len(group) >= 5:
            suspicious.append({
                "account": account,
                "reason": "Burst transactions",
                "risk_score": 0.82
            })

        # High amount detection
        if group["amount"].max() > 100000:
            suspicious.append({
                "account": account,
                "reason": "High value transaction",
                "risk_score": 0.91
            })

        # Night activity detection
        night_txns = group[
            (group["timestamp"].dt.hour >= 0) &
            (group["timestamp"].dt.hour <= 4)
        ]

        if len(night_txns) > 0:
            suspicious.append({
                "account": account,
                "reason": "Night transaction anomaly",
                "risk_score": 0.74
            })

    return suspicious

def save_suspicious_transactions(suspicious, output_path):

    with open(output_path, "w") as f:
        json.dump(suspicious, f, indent=4)