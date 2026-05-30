# fir_preprocessor.py

import uuid
import json
import spacy
from dateutil import parser

# Load SpaCy English model
# Install:
# pip install spacy python-dateutil
# python -m spacy download en_core_web_sm

nlp = spacy.load("en_core_web_sm")


# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------


# Generate a temporary ID for entities (since we don't have a real database ID yet)
def generate_temp_id(prefix="TEMP"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# Extract datetime/time entities from text using SpaCy and dateparser... It could be done better with regex, but let's keep it simple for now.
def extract_time(text):
    """
    Extract datetime/time entities from text
    """
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ in ["TIME", "DATE"]:
            try:
                parsed = parser.parse(ent.text)
                return parsed.isoformat()
            except:
                return ent.text

    return None


# ---------------------------------------------------
# Main FIR Preprocessor
# ---------------------------------------------------

def preprocess_fir(fir_text):

    doc = nlp(fir_text)

    entities = []
    relations = []

    entity_map = {}

    # ---------------------------------------------------
    # STEP 1 — Extract PERSON and LOCATION entities
    # ---------------------------------------------------

    for ent in doc.ents:

        if ent.label_ in ["PERSON", "GPE", "LOC", "FAC"]:

            entity_type = ("PERSON" if ent.label_ == "PERSON" else "LOCATION")

            temp_id = generate_temp_id()

            entity_obj = {
                "temp_id": temp_id,
                "type": entity_type,
                "attributes": {
                    "name": ent.text
                },
                "confidence": 0.90,
                "source": "fir_document"
            }

            entities.append(entity_obj)

            entity_map[ent.text] = temp_id

    # ---------------------------------------------------
    # STEP 2 — Very Basic Relation Extraction
    # ---------------------------------------------------

    # Example logic:
    # "Rahul met Arjun near Park Street at 9 PM"

    persons = [
        e for e in entities
        if e["type"] == "PERSON"
    ]

    locations = [
        e for e in entities
        if e["type"] == "LOCATION"
    ]

    timestamp = extract_time(fir_text)

    # PERSON ↔ PERSON relation
    if len(persons) >= 2:
        relation_obj = {
            "source": persons[0]["temp_id"],
            "target": persons[1]["temp_id"],
            "relation": "INTERACTED_WITH",
            "attributes": {},
            "timestamp": timestamp,
            "confidence": 0.75,
            "source_type": "fir_document"
        }

        relations.append(relation_obj)

    # PERSON ↔ LOCATION relation
    if len(persons) >= 1 and len(locations) >= 1:

        relation_obj = {
            "source": persons[0]["temp_id"],
            "target": locations[0]["temp_id"],
            "relation": "VISITED",
            "attributes": {},
            "timestamp": timestamp,
            "confidence": 0.70,
            "source_type": "fir_document"
        }

        relations.append(relation_obj)

    # ---------------------------------------------------
    # FINAL OUTPUT
    # ---------------------------------------------------

    output = {
        "entities": entities,
        "relations": relations
    }

    return output


# ---------------------------------------------------
# Example FIR Input
# ---------------------------------------------------

fir_text = """
Rahul met Arjun near Park Street at 9 PM.
Later Rahul transferred money to Vikram.
"""

# Run preprocessing
graph_objects = preprocess_fir(fir_text)

# Pretty print JSON
print(json.dumps(graph_objects, indent=4))