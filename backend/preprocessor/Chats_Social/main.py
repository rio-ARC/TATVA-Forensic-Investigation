"""
main.py — Unified Tatva communication preprocessing runner.

This file:
1. Detects input type automatically
2. Runs the correct preprocessor
3. Merges outputs from multiple files
4. Deduplicates entities
5. Produces one combined graph:
   {
      "entities": [...],
      "relations": [...]
   }

Supported inputs:
- WhatsApp / Telegram chat exports (.txt)
- Emails (.eml / .txt)
- Social media JSON exports (.json)

Usage:
    python main.py sample_data/chat.txt
    python main.py sample_data/email.eml
    python main.py sample_data/social.json

    OR multiple files:

    python main.py file1.txt file2.eml file3.json
"""

import json
import sys
from pathlib import Path

from .chat_preprocessor import preprocess_chat
from .email_preprocessor import preprocess_email
from .social_preprocessor import preprocess_social


# ---------------------------------------------------------------------------
# 1. File-type detector
# ---------------------------------------------------------------------------

def detect_file_type(filepath: str) -> str:
    """
    Detect which preprocessor should handle the file.

    Returns:
        "chat"
        "email"
        "social"
        None
    """

    path = Path(filepath)

    if not path.exists():
        return None

    ext = path.suffix.lower()

    # ---------------------------------------------------------
    # JSON → Social media posts
    # ---------------------------------------------------------
    if ext == ".json":
        return "social"

    # ---------------------------------------------------------
    # EML → Email
    # ---------------------------------------------------------
    if ext == ".eml":
        return "email"

    # ---------------------------------------------------------
    # TXT → Need content inspection
    # ---------------------------------------------------------
    if ext == ".txt":

        try:
            sample = path.read_text(encoding="utf-8", errors="replace")[:3000].lower()

        except Exception:
            return None

        # -----------------------------------------------------
        # Detect email-style headers
        # -----------------------------------------------------
        if (
            "from:" in sample and
            "to:" in sample and
            "subject:" in sample
        ):
            return "email"

        # -----------------------------------------------------
        # Detect WhatsApp / Telegram patterns
        # -----------------------------------------------------
        if "[" in sample and "]" in sample and ":" in sample:
            return "chat"

    return None


# ---------------------------------------------------------------------------
# 2. Entity deduplication
# ---------------------------------------------------------------------------

def entity_signature(entity: dict) -> tuple:
    """
    Generate a stable signature for deduplication.

    Example:
        PERSON + Rahul
        EMAIL_ADDRESS + abc@gmail.com
    """

    etype = entity["type"]
    attrs = entity["attributes"]

    # Priority keys
    for key in [
        "email",
        "number",
        "handle",
        "name",
        "address",
    ]:
        if key in attrs and attrs[key]:
            return (etype, str(attrs[key]).lower())

    return (etype, json.dumps(attrs, sort_keys=True))


def deduplicate_entities(entities: list):
    """
    Deduplicate entities and remap old temp_ids.

    Returns:
        deduped_entities,
        old_to_new_id_map
    """

    unique = {}
    id_map = {}

    for ent in entities:

        sig = entity_signature(ent)

        # First occurrence
        if sig not in unique:
            unique[sig] = ent

        # Map old id -> canonical id
        id_map[ent["temp_id"]] = unique[sig]["temp_id"]

    return list(unique.values()), id_map


# ---------------------------------------------------------------------------
# 3. Relation remapping
# ---------------------------------------------------------------------------

def remap_relations(relations: list, id_map: dict) -> list:
    """
    Replace old entity temp_ids with deduplicated canonical ids.
    """

    remapped = []

    for rel in relations:

        rel["source"] = id_map.get(rel["source"], rel["source"])
        rel["target"] = id_map.get(rel["target"], rel["target"])

        remapped.append(rel)

    return remapped


# ---------------------------------------------------------------------------
# 4. Main orchestration
# ---------------------------------------------------------------------------

def process_file(filepath: str) -> dict:
    """
    Run the correct preprocessor based on file type.
    """

    ftype = detect_file_type(filepath)

    if ftype == "chat":
        print(f"[INFO] Processing CHAT file: {filepath}")
        return preprocess_chat(filepath)

    elif ftype == "email":
        print(f"[INFO] Processing EMAIL file: {filepath}")
        return preprocess_email(filepath)

    elif ftype == "social":
        print(f"[INFO] Processing SOCIAL file: {filepath}")
        return preprocess_social(filepath)

    else:
        print(f"[WARNING] Unsupported or unknown file type: {filepath}")
        return {"entities": [], "relations": []}


# ---------------------------------------------------------------------------
# 5. Unified pipeline
# ---------------------------------------------------------------------------

def preprocess_socials(filepaths: list) -> dict:
    """
    Process all files and merge into one graph.
    """

    all_entities = []
    all_relations = []

    # ---------------------------------------------------------
    # Process each file independently
    # ---------------------------------------------------------
    for filepath in filepaths:

        result = process_file(filepath)

        all_entities.extend(result["entities"])
        all_relations.extend(result["relations"])

    # ---------------------------------------------------------
    # Deduplicate entities
    # ---------------------------------------------------------
    deduped_entities, id_map = deduplicate_entities(all_entities)

    # ---------------------------------------------------------
    # Remap relations
    # ---------------------------------------------------------
    final_relations = remap_relations(all_relations, id_map)

    return {
        "entities": deduped_entities,
        "relations": final_relations,
    }


# ---------------------------------------------------------------------------
# 6. Standalone CLI runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # run in terminal: python main.py file1.txt file2.txt file3.json
    if len(sys.argv) < 2:
        print(
            "\nUsage:\n"
            "python main.py <file1> <file2> ...\n"
        )
        sys.exit(1)

    input_files = sys.argv[1:]

    # input_files: list of file paths --> input_files = ["sample_data/chat.txt", "sample_data/social.json"]
    graph_output = preprocess_socials(input_files)

    print("\n================ COMBINED GRAPH OUTPUT ================\n")

    print(
        json.dumps(
            graph_output,
            indent=2,
            ensure_ascii=False
        )
    )