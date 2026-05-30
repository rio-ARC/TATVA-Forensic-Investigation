import spacy
import uuid
import json
import dateparser

nlp = spacy.load("en_core_web_sm")

# ------------------------------------------------
# RELATION VERB MAP
# ------------------------------------------------

RELATION_VERBS = {
    "meet": "INTERACTED_WITH",
    "call": "CALLED",
    "transfer": "TRANSFERRED_MONEY",
    "visit": "VISITED"
}

# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def generate_temp_id(prefix="TEMP"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def extract_timestamp(sentence):

    for ent in sentence.ents:

        if ent.label_ in ["TIME", "DATE"]:

            parsed = dateparser.parse(ent.text)

            if parsed:
                return parsed.isoformat()

    return None


def get_entity_text(token):
    for ent in token.doc.ents:
        if token.i >= ent.start and token.i < ent.end:
            return ent.text
    return token.text


# ------------------------------------------------
# MAIN PREPROCESSOR
# ------------------------------------------------

def preprocess_fir(text):

    doc = nlp(text)

    entities = []
    relations = []

    entity_lookup = {}

    # ------------------------------------------------
    # STEP 1 — EXTRACT LOCATIONS FIRST
    # ------------------------------------------------

    location_tokens = set()

    for ent in doc.ents:

        if ent.label_ in ["GPE", "LOC", "FAC"]:

            temp_id = generate_temp_id()

            entity_obj = {
                "temp_id": temp_id,
                "type": "LOCATION",
                "attributes": {
                    "name": ent.text
                },
                "confidence": 0.90,
                "source": "fir_document"
            }

            entities.append(entity_obj)

            entity_lookup[ent.text] = entity_obj

            # Store location tokens
            for token in ent:
                location_tokens.add(token.text)

    # ------------------------------------------------
    # STEP 2 — EXTRACT PERSONS
    # ------------------------------------------------

    for ent in doc.ents:

        # Only NER-recognized PERSON entities
        if ent.label_ == "PERSON":

            entity_name = ent.text

            if entity_name not in entity_lookup:

                temp_id = generate_temp_id()

                entity_obj = {
                    "temp_id": temp_id,
                    "type": "PERSON",
                    "attributes": {
                        "name": entity_name
                    },
                    "confidence": 0.90,
                    "source": "fir_document"
                }

                entities.append(entity_obj)

                entity_lookup[entity_name] = entity_obj

    # ------------------------------------------------
    # STEP 3 — RELATION EXTRACTION
    # ------------------------------------------------

    for sentence in doc.sents:

        subject = None
        obj = None
        relation_type = None

        timestamp = extract_timestamp(sentence)

        for token in sentence:

            # Detect relation verb
            if token.lemma_.lower() in RELATION_VERBS:

                relation_type = RELATION_VERBS[token.lemma_.lower()]

                # Dependency parsing
                for child in token.children:

                    # Subject
                    if child.dep_ == "nsubj":

                        subject = get_entity_text(child)

                    # Object
                    elif child.dep_ in ["dobj", "pobj", "obj"]:

                        obj = get_entity_text(child)

        # ------------------------------------------------
        # BUILD RELATION OBJECT
        # ------------------------------------------------

        if (
            subject in entity_lookup
            and obj in entity_lookup
            and relation_type
        ):

            source_entity = entity_lookup[subject]
            target_entity = entity_lookup[obj]

            relation_obj = {
                "source": source_entity["temp_id"],
                "target": target_entity["temp_id"],
                "relation": relation_type,
                "attributes": {},
                "timestamp": timestamp,
                "confidence": 0.75,
                "source_type": "fir_document"
            }

            relations.append(relation_obj)

    # ------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------

    output = {
        "entities": entities,
        "relations": relations
    }

    return output



# ------------------------------------------------
# RUN
# ------------------------------------------------

import json
import os

if __name__ == "__main__":

    
    with open("fir_data.txt", "r") as f:
        fir_text = f.read()

    graph_objects = preprocess_fir(fir_text)
    
    # Save to current working directory
    output_path = os.path.join(os.getcwd(), "graph_objects.json")
    
    with open(output_path, 'w') as f:
        json.dump(graph_objects, f, indent=4)
    
    print(f"JSON saved to: {output_path}")