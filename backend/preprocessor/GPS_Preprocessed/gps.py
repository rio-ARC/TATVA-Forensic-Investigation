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

def preprocess_gps(file_path, mapping=None):
    """
    Process a GPS location log file into entities and relations.

    Args:
        file_path: Path to the CSV/XLSX/JSON file.
        mapping:   Optional dict {canonical_col: raw_col}.
                   When provided, raw column names are translated via the mapping.
                   When None (default), canonical column names are expected directly
                   (backward-compatible).

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

    elif file_path.endswith(".json"):
        df = pd.read_json(file_path)

    else:
        raise ValueError("Unsupported file format")

    # ------------------------------------------------
    # COLUMN ACCESSOR HELPER
    # ------------------------------------------------

    def raw(canonical_name):
        """Return the actual column name to use for a canonical field."""
        if mapping and canonical_name in mapping:
            raw_col = mapping[canonical_name]
            if raw_col in df.columns:
                return raw_col
        if canonical_name in df.columns:
            return canonical_name
        return None  # column absent

    # ------------------------------------------------
    # STORAGE
    # ------------------------------------------------

    entities = []
    relations = []

    entity_lookup = {}

    previous_locations = {}

    # Resolve column names once
    device_id_col   = raw("device_id")
    latitude_col    = raw("latitude")
    longitude_col   = raw("longitude")
    timestamp_col   = raw("timestamp")
    accuracy_col    = raw("accuracy")
    speed_col       = raw("speed")
    source_col      = raw("source")

    # Also check legacy multi-identifier columns that gps.py originally supported
    phone_col   = raw("phone_number")
    vehicle_col = raw("vehicle_id")
    watch_col   = raw("watch_id")
    tracker_col = raw("tracker_id")

    # ------------------------------------------------
    # ITERATE RECORDS
    # ------------------------------------------------

    for _, row in df.iterrows():

        # ------------------------------------------------
        # ENTITY IDENTIFICATION (flexible)
        # ------------------------------------------------

        tracked_entity_id = None
        tracked_entity_type = "UNKNOWN_DEVICE"

        if device_id_col and pd.notna(row.get(device_id_col)):
            tracked_entity_id = str(row[device_id_col])
            tracked_entity_type = "DEVICE"

        elif phone_col and pd.notna(row.get(phone_col)):
            tracked_entity_id = str(row[phone_col])
            tracked_entity_type = "PHONE_NUMBER"

        elif vehicle_col and pd.notna(row.get(vehicle_col)):
            tracked_entity_id = str(row[vehicle_col])
            tracked_entity_type = "VEHICLE"

        elif watch_col and pd.notna(row.get(watch_col)):
            tracked_entity_id = str(row[watch_col])
            tracked_entity_type = "WEARABLE_DEVICE"

        elif tracker_col and pd.notna(row.get(tracker_col)):
            tracked_entity_id = str(row[tracker_col])
            tracked_entity_type = "TRACKER"

        else:
            continue

        # ------------------------------------------------
        # REQUIRED LOCATION FIELDS
        # ------------------------------------------------

        try:
            latitude  = float(row[latitude_col])
            longitude = float(row[longitude_col])

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

        timestamp = normalize_timestamp(row[timestamp_col] if timestamp_col else None)
        accuracy  = float(row[accuracy_col]) if accuracy_col and pd.notna(row.get(accuracy_col)) else 0.0
        speed     = float(row[speed_col])    if speed_col   and pd.notna(row.get(speed_col))    else 0.0
        source    = str(row[source_col])     if source_col  and pd.notna(row.get(source_col))   else "gps_analysis"

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
    graph_objects = preprocess_gps("gps_data_short.csv")

    print(json.dumps(graph_objects, indent=4))