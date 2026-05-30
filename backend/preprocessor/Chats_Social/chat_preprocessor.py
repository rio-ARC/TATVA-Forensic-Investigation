"""
chat_preprocessor.py — Parses WhatsApp and Telegram chat export .txt files
into the Tatva standard {entities, relations} graph output.
"""

import re
import json
from pathlib import Path

from .communication_utils import (
    load_nlp_model,
    extract_entities_from_text,
    make_entity,
    make_relation,
    normalize_timestamp,
)

# ---------------------------------------------------------------------------
# Regex patterns for supported chat formats
# ---------------------------------------------------------------------------

# WhatsApp 12-hour: [01/03/2024, 09:00 PM] Sender: text
_WA_12H = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2}\s*[AP]M)\]\s*([^:]+):\s*(.+)$',
    re.IGNORECASE,
)

# WhatsApp 24-hour: [01/03/2024, 21:00] Sender: text
_WA_24H = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2})\]\s*([^:]+):\s*(.+)$',
)

# Telegram: [21:00, 01/03/2024] Sender: text
_TG = re.compile(
    r'^\[(\d{1,2}:\d{2}),\s*(\d{1,2}/\d{1,2}/\d{4})\]\s*([^:]+):\s*(.+)$',
)

# Coded-language keyword sets (lowercased)
_URGENCY_WORDS    = {"abhi", "jaldi", "turant", "now", "immediately"}
_MONEY_WORDS      = {"paisa", "amount", "transfer", "bhej", "send"}
_TARGET_WORDS     = {"target", "number", "account", "wala"}
_COORD_WORDS      = {"ready", "confirm", "done", "ho gaya"}


# ---------------------------------------------------------------------------
# 1. Chat file parser
# ---------------------------------------------------------------------------

def parse_chat_file(filepath: str) -> list:
    """Read a chat export file and return a list of structured message dicts."""
    messages = []
    index = 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue

            msg = None

            # Try WhatsApp 12-hour
            m = _WA_12H.match(line)
            if m:
                date_str, time_str, sender, text = m.groups()
                raw_ts = f"{date_str} {time_str}"
                msg = {
                    "index": index,
                    "sender": sender.strip(),
                    "timestamp": normalize_timestamp(raw_ts),
                    "text": text.strip(),
                    "raw_line": raw_line.rstrip(),
                }

            # Try WhatsApp 24-hour
            if msg is None:
                m = _WA_24H.match(line)
                if m:
                    date_str, time_str, sender, text = m.groups()
                    raw_ts = f"{date_str} {time_str}"
                    msg = {
                        "index": index,
                        "sender": sender.strip(),
                        "timestamp": normalize_timestamp(raw_ts),
                        "text": text.strip(),
                        "raw_line": raw_line.rstrip(),
                    }

            # Try Telegram
            if msg is None:
                m = _TG.match(line)
                if m:
                    time_str, date_str, sender, text = m.groups()
                    raw_ts = f"{date_str} {time_str}"
                    msg = {
                        "index": index,
                        "sender": sender.strip(),
                        "timestamp": normalize_timestamp(raw_ts),
                        "text": text.strip(),
                        "raw_line": raw_line.rstrip(),
                    }

            if msg is not None:
                messages.append(msg)
                index += 1
            # else: system message / media omitted — silently skip

    return messages


# ---------------------------------------------------------------------------
# 2. Sender entity builder
# ---------------------------------------------------------------------------

def build_sender_entity(sender_name: str, source_file: str) -> dict:
    """Create a PERSON entity for a chat sender using make_entity()."""
    return make_entity(
        entity_type="PERSON",
        attributes={"name": sender_name, "platform": "chat"},
        confidence=0.90,
        source=source_file,
    )


# ---------------------------------------------------------------------------
# 3. Message relation builder
# ---------------------------------------------------------------------------

def build_message_relation(sender_entity: dict, receiver_entity: dict,
                           message: dict, source_file: str) -> dict:
    """Build a MESSAGED relation from sender to receiver for a single message."""
    return make_relation(
        source_id=sender_entity["temp_id"],
        target_id=receiver_entity["temp_id"],
        relation="MESSAGED",
        attributes={
            "text": message["text"],
            "platform": "whatsapp/telegram",
            "message_index": message["index"],
        },
        timestamp=message["timestamp"],
        confidence=0.95,
        provenance=f"{source_file}:message_{message['index']}",
    )


# ---------------------------------------------------------------------------
# 4. Coded-language detector
# ---------------------------------------------------------------------------

def detect_coded_language(text: str) -> dict:
    """Check message text for forensic signals using lowercased keyword matching."""
    lower = text.lower()
    words = set(re.findall(r"[a-zA-Z\u0900-\u097F]+", lower))

    return {
        "has_urgency":      bool(words & _URGENCY_WORDS),
        "has_money_ref":    bool(words & _MONEY_WORDS),
        "has_target_ref":   bool(words & _TARGET_WORDS),
        "has_coordination": bool(words & _COORD_WORDS),
    }


# ---------------------------------------------------------------------------
# 5. Main pipeline entry point
# ---------------------------------------------------------------------------

def preprocess_chat(filepath: str) -> dict:
    """Orchestrate full chat preprocessing pipeline; return {entities, relations}."""
    source_file = Path(filepath).name
    messages = parse_chat_file(filepath)

    entities = []
    relations = []

    # --- Build one PERSON entity per unique sender ---
    sender_entities = {}   # sender_name -> entity dict
    for msg in messages:
        name = msg["sender"]
        if name not in sender_entities:
            ent = build_sender_entity(name, source_file)
            sender_entities[name] = ent
            entities.append(ent)

    unique_senders = list(sender_entities.keys())
    is_group_chat = len(unique_senders) >= 3

    # --- Determine target: peer or group entity ---
    if is_group_chat:
        group_entity = make_entity(
            entity_type="PLATFORM",
            attributes={"name": "group_chat"},
            confidence=1.0,
            source=source_file,
        )
        entities.append(group_entity)

    # --- Per-message processing ---
    for msg in messages:
        sender_ent = sender_entities[msg["sender"]]

        # Determine receiver
        if is_group_chat:
            receiver_ent = group_entity
        else:
            # Direct chat: the other participant
            other_names = [n for n in unique_senders if n != msg["sender"]]
            if not other_names:
                continue
            receiver_ent = sender_entities[other_names[0]]

        # Forensic signals
        signals = detect_coded_language(msg["text"])

        # Build MESSAGED relation
        rel = build_message_relation(sender_ent, receiver_ent, msg, source_file)
        rel["attributes"]["forensic_signals"] = signals
        relations.append(rel)

        # Inline entity extraction from message text
        inline_entities = extract_entities_from_text(msg["text"], source_file)
        for ie in inline_entities:
            entities.append(ie)
            # MENTIONED relation: sender → inline entity
            relations.append(make_relation(
                source_id=sender_ent["temp_id"],
                target_id=ie["temp_id"],
                relation="MENTIONED",
                attributes={"message_index": msg["index"]},
                timestamp=msg["timestamp"],
                confidence=0.75,
                provenance=f"{source_file}:message_{msg['index']}",
            ))

    return {"entities": entities, "relations": relations}


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    result = preprocess_chat(
        sys.argv[1] if len(sys.argv) > 1 else "sample_data/sample_chat.txt"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
