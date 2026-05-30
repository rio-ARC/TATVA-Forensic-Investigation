# investigator_annotations.py

import csv
import uuid

# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def generate_annotation_id():
    return f"ANNOT_{uuid.uuid4().hex[:8]}"


# ------------------------------------------------
# LOAD ANNOTATIONS
# ------------------------------------------------

def load_annotations(annotation_path):

    annotations = []

    with open(annotation_path, "r", newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)
        
        if reader.fieldnames is None:
            raise ValueError(
                f"CSV file at '{annotation_path}' is empty or invalid."
            )
            
        # Normalize and clean actual headers
        clean_fieldnames = [name.strip().lower() for name in reader.fieldnames if name]
        
        # Verify required headers exist
        required_headers = ["source_entity", "target_entity", "relation"]
        missing = [req for req in required_headers if req not in clean_fieldnames]
        
        if missing:
            raise ValueError(
                f"\n[ERROR] CSV Headings Mismatch in '{annotation_path}'!\n"
                f"Expected headings: {', '.join(required_headers)}\n"
                f"Missing required headings: {', '.join(missing)}\n"
                f"Detected headings in your CSV: {', '.join(reader.fieldnames)}\n"
                f"Please check your CSV headers and try again.\n"
            )

        for row in reader:
            # Re-key row using standardized lowercase and stripped keys
            clean_row = {}
            for k, v in row.items():
                if k:
                    clean_row[k.strip().lower()] = v

            # Parse confidence
            confidence_val = clean_row.get("confidence")
            if confidence_val:
                try:
                    clean_row["confidence"] = float(confidence_val)
                except ValueError:
                    clean_row["confidence"] = 0.95
            else:
                clean_row["confidence"] = 0.95

            # Set evidence default if not present
            if "evidence" not in clean_row:
                clean_row["evidence"] = "investigator_annotation"

            annotations.append(clean_row)

    return annotations


# ------------------------------------------------
# BUILD ANNOTATION RELATIONS
# ------------------------------------------------

def build_annotation_relations(
    annotations,
    entity_lookup
):

    annotation_relations = []

    for annotation in annotations:

        source_value = (
            annotation["source_entity"]
            .strip()
            .lower()
        )

        target_value = (
            annotation["target_entity"]
            .strip()
            .lower()
        )

        relation_type = annotation["relation"]

        confidence = annotation.get(
            "confidence",
            0.95
        )

        evidence = annotation.get(
            "evidence",
            "investigator_annotation"
        )

        # ------------------------------------------------
        # FIND MATCHING ENTITIES
        # ------------------------------------------------

        source_id = None
        target_id = None

        for entity_id, entity in entity_lookup.items():

            entity_type = entity.get("type")

            attributes = entity.get(
                "attributes",
                {}
            )

            # PERSON
            if entity_type == "PERSON":

                name = (
                    attributes.get("name", "")
                    .strip()
                    .lower()
                )

                if name == source_value:
                    source_id = entity_id

                if name == target_value:
                    target_id = entity_id

            # PHONE
            elif entity_type == "PHONE_NUMBER":

                number = str(
                    attributes.get("number")
                    or attributes.get("identifier")
                    or ""
                ).replace(".0", "").strip()

                if number == source_value:
                    source_id = entity_id

                if number == target_value:
                    target_id = entity_id

            # EMAIL
            elif entity_type == "EMAIL":

                email = (
                    attributes.get("email", "")
                    .strip()
                    .lower()
                )

                if email == source_value:
                    source_id = entity_id

                if email == target_value:
                    target_id = entity_id

            # DEVICE TYPES
            elif entity_type in [
                "DEVICE",
                "VEHICLE",
                "TRACKER",
                "WEARABLE_DEVICE"
            ]:

                identifier = (
                    attributes.get(
                        "identifier",
                        ""
                    )
                    .strip()
                    .lower()
                )

                if identifier == source_value:
                    source_id = entity_id

                if identifier == target_value:
                    target_id = entity_id

            # ACCOUNT
            elif entity_type == "ACCOUNT":

                acc_id = str(
                    attributes.get("account_id")
                    or entity.get("temp_id")
                    or entity.get("id")
                    or ""
                ).strip().lower()

                if acc_id == source_value:
                    source_id = entity_id

                if acc_id == target_value:
                    target_id = entity_id

            # LOCATION
            elif entity_type == "LOCATION":

                name = (
                    attributes.get("name", "")
                    .strip()
                    .lower()
                )

                lat = attributes.get("latitude")
                lon = attributes.get("longitude")

                coordinates = None
                resolved_name = None

                if lat and lon:
                    coordinates = f"{lat},{lon}"
                    from entity_resolution import resolve_coordinates_dynamically
                    try:
                        resolved_name = resolve_coordinates_dynamically(float(lat), float(lon))
                    except Exception:
                        pass

                # Match if names match, coordinates match, coordinate prefix matches (e.g. "22.5726" matching "22.5726,88.3639"), 
                # or if the dynamic resolved name matches the annotation's name/value!
                if (
                    name == source_value
                    or (coordinates and (coordinates == source_value or coordinates.startswith(source_value)))
                    or (resolved_name and resolved_name == source_value)
                ):
                    source_id = entity_id

                if (
                    name == target_value
                    or (coordinates and (coordinates == target_value or coordinates.startswith(target_value)))
                    or (resolved_name and resolved_name == target_value)
                ):
                    target_id = entity_id

        # ------------------------------------------------
        # CREATE RELATION
        # ------------------------------------------------

        if source_id and target_id:

            relation = {
                "annotation_id": generate_annotation_id(),

                "source": source_id,

                "target": target_id,

                "relation": relation_type,

                "attributes": {
                    "evidence": evidence
                },

                "confidence": confidence,

                "source_type":
                    "investigator_annotation"
            }

            annotation_relations.append(
                relation
            )

    return annotation_relations
