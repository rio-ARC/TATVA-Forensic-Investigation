import pandas as pd
import uuid
import json
from math import radians, sin, cos, sqrt, atan2

# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def generate_temp_id(prefix="TEMP"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def calculate_distance(lat1, lon1, lat2, lon2):

    """
    Calculate distance between two coordinates in meters
    using Haversine Formula
    """

    R = 6371000  # Earth radius in meters

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def normalize_timestamp(timestamp):

    try:
        return pd.to_datetime(timestamp).isoformat()

    except (ValueError, TypeError):
        return None


# ------------------------------------------------
# MAIN PREPROCESSOR
# ------------------------------------------------

def preprocess_gps(file_path):

    # ------------------------------------------------
    # LOAD FILE
    # ------------------------------------------------

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)

    elif file_path.endswith(".json"):
        df = pd.read_json(file_path)

    else:
        raise ValueError("Unsupported file format")

    # ------------------------------------------------
    # STORAGE
    # ------------------------------------------------

    entities = []
    relations = []

    entity_lookup = {}

    previous_locations = {}

    # ------------------------------------------------
    # ITERATE RECORDS
    # ------------------------------------------------

    for _, row in df.iterrows():

        # ------------------------------------------------
        # FLEXIBLE IDENTIFIER HANDLING
        # ------------------------------------------------

        tracked_entity_id = None
        tracked_entity_type = "UNKNOWN_DEVICE"

        # Mobile device
        if "device_id" in row and pd.notna(row["device_id"]):

            tracked_entity_id = str(row["device_id"])
            tracked_entity_type = "DEVICE"

        # Phone number
        elif "phone_number" in row and pd.notna(row["phone_number"]):

            tracked_entity_id = str(row["phone_number"])
            tracked_entity_type = "PHONE_NUMBER"

        # Vehicle
        elif "vehicle_id" in row and pd.notna(row["vehicle_id"]):

            tracked_entity_id = str(row["vehicle_id"])
            tracked_entity_type = "VEHICLE"

        # Smart watch
        elif "watch_id" in row and pd.notna(row["watch_id"]):

            tracked_entity_id = str(row["watch_id"])
            tracked_entity_type = "WEARABLE_DEVICE"

        # Generic tracker
        elif "tracker_id" in row and pd.notna(row["tracker_id"]):

            tracked_entity_id = str(row["tracker_id"])
            tracked_entity_type = "TRACKER"

        else:
            continue

        # ------------------------------------------------
        # REQUIRED LOCATION FIELDS
        # ------------------------------------------------

        try:

            latitude = float(row["latitude"])
            longitude = float(row["longitude"])

        except (ValueError, TypeError, KeyError):
            continue

        # ------------------------------------------------
        # VALIDATE COORDINATES
        # ------------------------------------------------

        if not (-90 <= latitude <= 90):
            continue

        if not (-180 <= longitude <= 180):
            continue

        # ------------------------------------------------
        # OPTIONAL FIELDS
        # ------------------------------------------------

        timestamp = normalize_timestamp(row.get("timestamp", None))

        accuracy = float(row.get("accuracy", 0))

        speed = float(row.get("speed", 0))

        source = str(row.get("source", "unknown_source"))

        # ------------------------------------------------
        # CREATE TRACKED ENTITY NODE
        # ------------------------------------------------

        if tracked_entity_id not in entity_lookup:

            entity_temp_id = generate_temp_id(tracked_entity_type)

            tracked_entity = {
                "temp_id": entity_temp_id,
                "type": tracked_entity_type,
                "attributes": {
                    "identifier": tracked_entity_id
                },
                "confidence": 0.99,
                "source": source
            }

            entities.append(tracked_entity)

            entity_lookup[tracked_entity_id] = tracked_entity

        # ------------------------------------------------
        # CREATE LOCATION NODE
        # ------------------------------------------------

        location_key = f"{latitude}_{longitude}"

        if location_key not in entity_lookup:

            location_temp_id = generate_temp_id("LOCATION")

            location_entity = {
                "temp_id": location_temp_id,
                "type": "LOCATION",
                "attributes": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "confidence": 0.95,
                "source": source
            }

            entities.append(location_entity)

            entity_lookup[location_key] = location_entity

        # ------------------------------------------------
        # FETCH ENTITIES
        # ------------------------------------------------

        tracked_entity = entity_lookup[tracked_entity_id]

        location_entity = entity_lookup[location_key]

        # ------------------------------------------------
        # LOCATED_AT EDGE
        # ------------------------------------------------

        located_relation = {
            "source": tracked_entity["temp_id"],
            "target": location_entity["temp_id"],
            "relation": "LOCATED_AT",
            "attributes": {
                "accuracy": accuracy,
                "speed": speed
            },
            "timestamp": timestamp,
            "confidence": 0.95,
            "source_type": source
        }

        relations.append(located_relation)

        # ------------------------------------------------
        # MOVEMENT TRACKING
        # ------------------------------------------------

        if tracked_entity_id in previous_locations:

            previous = previous_locations[tracked_entity_id]

            distance = calculate_distance(
                previous["latitude"],
                previous["longitude"],
                latitude,
                longitude
            )

            movement_relation = {
                "source": previous["location_temp_id"],
                "target": location_entity["temp_id"],
                "relation": "MOVED_TO",
                "attributes": {
                    "distance_meters": round(distance, 2)
                },
                "timestamp": timestamp,
                "confidence": 0.90,
                "source_type": "gps_analysis"
            }

            relations.append(movement_relation)

        # ------------------------------------------------
        # STORE PREVIOUS LOCATION
        # ------------------------------------------------

        previous_locations[tracked_entity_id] = {
            "latitude": latitude,
            "longitude": longitude,
            "location_temp_id": location_entity["temp_id"]
        }

    # ------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------

    output = {
        "entities": entities,   # nodes
        "relations": relations   # edges
    }

    return output


# ------------------------------------------------
# TEST
# ------------------------------------------------

if __name__ == "__main__":
    # graph_objects = preprocess_gps("gps_data.csv")
    graph_objects = preprocess_gps("gps_data_short.csv")

    print(json.dumps(graph_objects, indent=4))