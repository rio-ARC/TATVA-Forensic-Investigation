import pandas as pd
import uuid
import json
import re

# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def generate_temp_id(prefix="TEMP"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def clean_phone_number(number):

    number = str(number)

    # Remove spaces, +91, -, etc.
    number = re.sub(r"\D", "", number)

    # Keep last 10 digits
    if len(number) > 10:
        number = number[-10:]

    return number


# ------------------------------------------------
# MAIN PREPROCESSOR
# ------------------------------------------------

def preprocess_cdr(file_path, mapping=None):
    """
    Process a CDR file into entities and relations.

    Args:
        file_path: Path to the CSV/XLSX file.
        mapping:   Optional dict {canonical_col: raw_col}.
                   When provided, the file is read with raw columns and
                   accessed via the mapping.
                   When None (default), the file is expected to already
                   use canonical column names (backward-compatible).

    Returns:
        {"entities": [...], "relations": [...]}
    """

    # ------------------------------------------------
    # LOAD FILE
    # ------------------------------------------------

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file format")

    # ------------------------------------------------
    # COLUMN ACCESSOR HELPER
    # ------------------------------------------------

    def col(canonical_name, default=None):
        """
        Return the raw column name to use for a given canonical column.
        Falls back to the canonical name itself (backward-compatible).
        """
        if mapping and canonical_name in mapping:
            raw = mapping[canonical_name]
            if raw in df.columns:
                return raw
        # canonical name used directly (no mapping, or already renamed)
        if canonical_name in df.columns:
            return canonical_name
        if default is not None:
            return None  # sentinel: use default value
        raise KeyError(
            f"[CDRPreprocessor] Column '{canonical_name}' not found. "
            f"mapping={mapping}, columns={list(df.columns)}"
        )

    # ------------------------------------------------
    # STORAGE
    # ------------------------------------------------

    entities = []
    relations = []

    entity_lookup = {}

    # ------------------------------------------------
    # PROCESS EACH RECORD
    # ------------------------------------------------

    for _, row in df.iterrows():

        caller_number = clean_phone_number(row[col("caller_number")])

        receiver_number = clean_phone_number(row[col("receiver_number")])

        timestamp = str(row[col("timestamp")])

        duration = int(row[col("duration")])

        # Optional fields — use schema defaults if column absent
        call_type_col = col("call_type", default="VOICE")
        call_type = str(row[call_type_col]).upper() if call_type_col else "VOICE"

        tower_id_col = col("tower_id", default="TWR_UNKNOWN")
        tower_id = str(row[tower_id_col]) if tower_id_col else "TWR_UNKNOWN"

        # ------------------------------------------------
        # CREATE CALLER NODE
        # ------------------------------------------------

        if caller_number not in entity_lookup:

            caller_temp_id = generate_temp_id("PHONE")

            caller_entity = {
                "temp_id": caller_temp_id,
                "type": "PHONE_NUMBER",
                "attributes": {
                    "number": caller_number
                },
                "confidence": 0.99,
                "source": "cdr_record"
            }

            entities.append(caller_entity)

            entity_lookup[caller_number] = caller_entity

        # ------------------------------------------------
        # CREATE RECEIVER NODE
        # ------------------------------------------------

        if receiver_number not in entity_lookup:

            receiver_temp_id = generate_temp_id("PHONE")

            receiver_entity = {
                "temp_id": receiver_temp_id,
                "type": "PHONE_NUMBER",
                "attributes": {
                    "number": receiver_number
                },
                "confidence": 0.99,
                "source": "cdr_record"
            }

            entities.append(receiver_entity)

            entity_lookup[receiver_number] = receiver_entity

        # ------------------------------------------------
        # CREATE TOWER NODE
        # ------------------------------------------------

        if tower_id not in entity_lookup:

            tower_temp_id = generate_temp_id("TOWER")

            tower_entity = {
                "temp_id": tower_temp_id,
                "type": "CELL_TOWER",
                "attributes": {
                    "tower_id": tower_id
                },
                "confidence": 0.95,
                "source": "cdr_record"
            }

            entities.append(tower_entity)

            entity_lookup[tower_id] = tower_entity

        # ------------------------------------------------
        # FETCH ENTITIES
        # ------------------------------------------------

        caller_entity = entity_lookup[caller_number]

        receiver_entity = entity_lookup[receiver_number]

        tower_entity = entity_lookup[tower_id]

        # ------------------------------------------------
        # CALL RELATION
        # ------------------------------------------------

        call_relation = {
            "source": caller_entity["temp_id"],
            "target": receiver_entity["temp_id"],
            "relation": "CALLED",
            "attributes": {
                "duration": duration,
                "call_type": call_type
            },
            "timestamp": timestamp,
            "confidence": 0.99,
            "source_type": "cdr_record"
        }

        relations.append(call_relation)

        # ------------------------------------------------
        # TOWER RELATION
        # ------------------------------------------------

        tower_relation = {
            "source": caller_entity["temp_id"],
            "target": tower_entity["temp_id"],
            "relation": "CONNECTED_TO_TOWER",
            "attributes": {},
            "timestamp": timestamp,
            "confidence": 0.95,
            "source_type": "cdr_record"
        }

        relations.append(tower_relation)

    # ------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------

    output = {
        "entities": entities,
        "relations": relations
    }

    return output


# ------------------------------------------------
# TEST
# ------------------------------------------------
if __name__ == "__main__":
    graph_objects = preprocess_cdr("cdr_records.csv")

    print(json.dumps(graph_objects, indent=4))