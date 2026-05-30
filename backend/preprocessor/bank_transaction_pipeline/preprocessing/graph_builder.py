import json

def build_graph(df, features, suspicious):

    nodes = []
    edges = []

    suspicious_accounts = {
        item["account"]: item["risk_score"] for item in suspicious
    }

    unique_accounts = set(df["sender_acc"]).union(
        set(df["receiver_acc"])
    )

    for acc in unique_accounts:

        node = {
            "temp_id": acc,
            "type": "ACCOUNT",
            "attributes": {
                "account_id": acc,
                "risk_score": suspicious_accounts.get(acc, 0.1),
                "features": features.get(acc, {})
            },
            "confidence": 0.95,
            "source": "bank_transaction"
        }

        nodes.append(node)

    for _, row in df.iterrows():

        edge = {
            "source": row["sender_acc"],
            "target": row["receiver_acc"],
            "relation": "TRANSFERRED_TO",
            "attributes": {
                "amount": row["amount"],
                "transaction_type": row["txn_type"],
                "location": row["location"]
            },
            "timestamp": str(row["timestamp"]),
            "confidence": 0.99,
            "source_type": "bank_transaction"
        }

        edges.append(edge)

    return nodes, edges


def save_graph(nodes, edges, node_path, edge_path):

    with open(node_path, "w") as f:
        json.dump(nodes, f, indent=4)

    with open(edge_path, "w") as f:
        json.dump(edges, f, indent=4)