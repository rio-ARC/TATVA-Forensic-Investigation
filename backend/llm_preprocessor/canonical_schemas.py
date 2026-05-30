"""
llm_preprocessor/canonical_schemas.py
======================================
Single source of truth for all canonical schemas.

Each schema defines:
  - required: columns the preprocessor MUST receive
  - optional: columns with fallback defaults
  - defaults: static fallback values for optional fields
"""

CANONICAL_SCHEMAS = {

    "CDR": {
        "required": ["caller_number", "receiver_number", "timestamp", "duration"],
        "optional": ["call_type", "tower_id"],
        "defaults": {
            "call_type": "VOICE",
            "tower_id": "TWR_UNKNOWN",
        },
    },

    "BANK_TRANSACTION": {
        "required": ["sender_acc", "receiver_acc", "amount", "timestamp"],
        "optional": ["txn_type", "location"],
        "defaults": {
            "txn_type": "TRANSFER",
            "location": "Unknown",
        },
    },

    "GPS": {
        "required": ["device_id", "latitude", "longitude", "timestamp"],
        "optional": ["accuracy", "speed", "source"],
        "defaults": {
            "accuracy": 0.0,
            "speed": 0.0,
            "source": "gps_analysis",
        },
    },

    "CHAT_LOG": {
        "required": ["sender", "receiver", "message", "timestamp"],
        "optional": ["channel", "platform"],
        "defaults": {
            "channel": "chat",
            "platform": "unknown",
        },
    },

    "EMAIL": {
        "required": ["sender", "recipient", "subject", "timestamp"],
        "optional": ["body", "channel"],
        "defaults": {
            "body": "",
            "channel": "email",
        },
    },
}

# Dataset types that require schema mapping (structured tabular files)
STRUCTURED_TYPES = {"CDR", "BANK_TRANSACTION", "GPS", "CHAT_LOG", "EMAIL"}

# Dataset types that are unstructured (use LLM extraction, not schema mapping)
UNSTRUCTURED_TYPES = {"FIR", "CASE_NOTES", "REPORT"}

# Minimum LLM confidence to proceed with schema mapping
CONFIDENCE_THRESHOLD = 0.70
