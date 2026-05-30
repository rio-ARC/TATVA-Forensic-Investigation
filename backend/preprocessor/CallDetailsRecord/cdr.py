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

def preprocess_cdr(file_path):

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
    # STORAGE
    # ------------------------------------------------

    entities = []
    relations = []

    entity_lookup = {}

    # ------------------------------------------------
    # PROCESS EACH RECORD
    # ------------------------------------------------

    for _, row in df.iterrows():

        caller_number = clean_phone_number(row["caller_number"])

        receiver_number = clean_phone_number(row["receiver_number"])

        timestamp = str(row["timestamp"])

        duration = int(row["duration"])

        call_type = str(row["call_type"]).upper()

        tower_id = str(row["tower_id"])

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