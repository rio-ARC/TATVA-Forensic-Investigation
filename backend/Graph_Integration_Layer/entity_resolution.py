# entity_resolution.py

import uuid
import os
import time
from collections import defaultdict
from math import radians, sin, cos, sqrt, atan2
import requests as _requests
import json

# ------------------------------------------------
# DYNAMIC COORDINATE RESOLVER  (API-only, no hardcoded landmarks)
# ------------------------------------------------

# In-memory cache (populated from disk/Redis on first use)
_GEO_CACHE = {}
_GEO_CACHE_LOADED = False

# Persistent cache files
_CACHE_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_FILES = [
    os.path.join(_CACHE_FILE_DIR, "geo_cache.json"),
    os.path.join(_CACHE_FILE_DIR, "output", "geo_cache.json")
]

# Nominatim requires ≤1 request/second
_last_request_time = 0.0
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            # Ensure backend is in python path
            import sys
            from pathlib import Path
            backend_path = str(Path(__file__).parent.parent)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            from db.redis_client import RedisClient
            _redis_client = RedisClient()
        except Exception as e:
            print(f"[Redis] Error initializing in entity_resolution: {e}")
            _redis_client = False
    return _redis_client

def _load_geo_cache():
    """Load the persistent geo-cache from disk into memory (once)."""
    global _GEO_CACHE, _GEO_CACHE_LOADED
    if _GEO_CACHE_LOADED:
        return
    
    # Try local files
    for cache_path in _CACHE_FILES:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # Keys are stored as "lat,lon" strings in JSON
                for k, v in raw.items():
                    parts = k.split(",")
                    _GEO_CACHE[(float(parts[0]), float(parts[1]))] = v
                print(f"[Geo Cache] Loaded {len(raw)} entries from {os.path.basename(cache_path)}")
                break # Stop at first found cache file
            except Exception:
                pass
                
    _GEO_CACHE_LOADED = True


def _save_geo_cache():
    """Persist the in-memory geo-cache to disk."""
    try:
        serialisable = {
            f"{lat},{lon}": name
            for (lat, lon), name in _GEO_CACHE.items()
        }
        # Save to both locations to ensure consistency
        for cache_path in _CACHE_FILES:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(serialisable, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2)**2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def resolve_coordinates_dynamically(lat, lon):
    """
    Resolve (lat, lon) → human-readable place name using the
    OpenStreetMap Nominatim reverse-geocoding API.

    Results are cached both in-memory/disk and Upstash Redis
    so the API is only called once per unique coordinate pair.
    """
    global _last_request_time

    _load_geo_cache()
    coord_key = (round(lat, 5), round(lon, 5))

    # 1. Check Upstash Redis cache first
    rc = _get_redis_client()
    if rc and rc.connected:
        try:
            cached_val = rc.get_geo(lat, lon)
            if cached_val:
                # Also sync back to in-memory cache if not present
                if coord_key not in _GEO_CACHE:
                    _GEO_CACHE[coord_key] = cached_val
                return cached_val
        except Exception as e:
            print(f"[Redis] Error getting geo cache: {e}")

    # 2. Check local in-memory cache
    if coord_key in _GEO_CACHE:
        # Sync back to Redis if Redis was missing it
        if rc and rc.connected:
            try:
                rc.set_geo(lat, lon, _GEO_CACHE[coord_key])
            except Exception:
                pass
        return _GEO_CACHE[coord_key]

    # 3. Call Nominatim reverse-geocoding API
    try:
        # Rate-limit: wait if last request was < 1 s ago
        elapsed = time.time() - _last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

        resp = _requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "TatvaForensics/1.0 (academic research project)"
            },
            timeout=5,
        )
        _last_request_time = time.time()
        resp.raise_for_status()
        data = resp.json()

        address = data.get("address", {})
        road    = address.get("road")
        suburb  = address.get("suburb") or address.get("neighbourhood")
        city    = (address.get("city")
                   or address.get("town")
                   or address.get("county"))

        parts = [p for p in [road, suburb, city] if p]
        if parts:
            resolved_str = ", ".join(parts).lower()
            # Cache locally
            _GEO_CACHE[coord_key] = resolved_str
            _save_geo_cache()
            # Cache in Redis
            if rc and rc.connected:
                try:
                    rc.set_geo(lat, lon, resolved_str)
                except Exception:
                    pass
            return resolved_str

        # If address parts are empty but display_name exists
        display = data.get("display_name")
        if display:
            # Take the first 3 comma-separated parts for brevity
            short = ", ".join(display.split(",")[:3]).strip().lower()
            _GEO_CACHE[coord_key] = short
            _save_geo_cache()
            if rc and rc.connected:
                try:
                    rc.set_geo(lat, lon, short)
                except Exception:
                    pass
            return short
    except Exception:
        pass

    # 4. Fallback to clean coordinate label
    fallback_str = f"location near {lat:.4f}n, {lon:.4f}e"
    _GEO_CACHE[coord_key] = fallback_str
    _save_geo_cache()
    if rc and rc.connected:
        try:
            rc.set_geo(lat, lon, fallback_str)
        except Exception:
            pass
    return fallback_str


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def generate_master_id():

    return f"MASTER_{uuid.uuid4().hex[:8]}"


# ------------------------------------------------
# EXTRACT ENTITY VALUE
# ------------------------------------------------

def extract_entity_value(entity):

    entity_type = entity.get("type")

    attributes = entity.get(
        "attributes",
        {}
    )

    # ------------------------------------------------
    # PERSON
    # ------------------------------------------------

    if entity_type == "PERSON":

        return (
            attributes.get("name", "")
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # PHONE
    # ------------------------------------------------

    elif entity_type == "PHONE_NUMBER":

        return (
            str(
                attributes.get("number")
                or attributes.get("identifier")
            )
            .replace(".0", "")
            .strip()
        )

    # ------------------------------------------------
    # EMAIL
    # ------------------------------------------------

    elif entity_type == "EMAIL":

        return (
            attributes.get("email", "")
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # ACCOUNT
    # ------------------------------------------------

    elif entity_type == "ACCOUNT":

        # support both old schema (id) and new schema (attributes.account_id)
        return (
            str(
                attributes.get("account_id")
                or entity.get("id")
                or ""
            )
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # DEVICES
    # ------------------------------------------------

    elif entity_type in [
        "DEVICE",
        "VEHICLE",
        "TRACKER",
        "WEARABLE_DEVICE"
    ]:

        return (
            attributes.get("identifier", "")
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # LOCATION
    # ------------------------------------------------

    elif entity_type == "LOCATION":

        name = attributes.get("name")

        if name:

            return (
                name
                .lower()
                .strip()
            )

        lat = attributes.get("latitude")

        lon = attributes.get("longitude")

        if lat and lon:
            try:
                return resolve_coordinates_dynamically(float(lat), float(lon))
            except Exception:
                return f"{lat},{lon}"

    # ------------------------------------------------
    # CELL TOWER
    # ------------------------------------------------

    elif entity_type == "CELL_TOWER":
        tower_id = attributes.get("tower_id") or entity.get("temp_id") or entity.get("id") or "unknown"
        return f"cell tower ({tower_id})".lower()

    # ------------------------------------------------
    # CAMERA
    # ------------------------------------------------

    elif entity_type == "CAMERA":
        loc = attributes.get("location")
        cam_id = entity.get("temp_id") or entity.get("id") or "unknown"
        if loc:
            loc_str = str(loc).replace("_", " ").title()
            return f"cctv camera at {loc_str}".lower()
        else:
            return f"cctv camera ({cam_id})".lower()

    # ------------------------------------------------
    # PLATFORM
    # ------------------------------------------------

    elif entity_type == "PLATFORM":

        return (
            attributes.get("name", "")
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # SOCIAL HANDLE
    # ------------------------------------------------

    elif entity_type == "SOCIAL_HANDLE":

        return (
            attributes.get("handle", "")
            .lower()
            .strip()
        )

    # ------------------------------------------------
    # UNIVERSAL FALLBACK
    # Any entity type not listed above still gets a
    # unique value so it ends up in resolved_mapping.
    # ------------------------------------------------

    fallback = entity.get("temp_id") or entity.get("id")

    if fallback:
        return str(fallback).lower().strip()

    return None


# ------------------------------------------------
# MERGE CLUSTERS
# ------------------------------------------------

def merge_clusters(
    cluster_a,
    cluster_b,
    clusters
):

    if cluster_a == cluster_b:
        return

    for entity_id in clusters[cluster_b]:

        clusters[cluster_a].add(entity_id)

    del clusters[cluster_b]


# ------------------------------------------------
# FUZZY NAME MERGE FOR PERSONS
# ------------------------------------------------

def fuzzy_merge_persons(clusters, entity_lookup, entity_to_cluster):

    """
    Merge PERSON clusters where one name is a substring of the other.
    Example: "rahul" and "rahul sen" → merged into one cluster.
    """

    # Collect one (cluster_id, name) per cluster that has a PERSON
    person_clusters = []

    for cluster_id, entity_ids in list(clusters.items()):

        for eid in entity_ids:

            entity = entity_lookup.get(eid)

            if entity and entity.get("type") == "PERSON":

                name = (
                    entity.get("attributes", {})
                    .get("name", "")
                    .lower()
                    .strip()
                )

                if name:
                    person_clusters.append((cluster_id, name))
                    break

    # Compare all pairs — merge if one name is a substring of the other
    merged = set()

    for i, (cid_a, name_a) in enumerate(person_clusters):

        if cid_a in merged or cid_a not in clusters:
            continue

        for j, (cid_b, name_b) in enumerate(person_clusters):

            if i >= j:
                continue

            if cid_b in merged or cid_b not in clusters:
                continue

            if cid_a == cid_b:
                continue

            # substring match: "rahul" in "rahul sen" or vice versa
            if name_a in name_b or name_b in name_a:

                merge_clusters(cid_a, cid_b, clusters)
                merged.add(cid_b)

                for eid in clusters[cid_a]:
                    entity_to_cluster[eid] = cid_a


# ------------------------------------------------
# ENTITY RESOLUTION
# ------------------------------------------------

def resolve_entities(
    entities,
    relations
):

    # ------------------------------------------------
    # ENTITY LOOKUP
    # ------------------------------------------------

    entity_lookup = {}

    for entity in entities:

        entity_id = (
            entity.get("temp_id")
            or entity.get("id")
        )

        entity_lookup[entity_id] = entity

    # ------------------------------------------------
    # INITIAL CLUSTERS
    # ------------------------------------------------

    clusters = {}

    entity_to_cluster = {}

    # ------------------------------------------------
    # VALUE-BASED GROUPING
    # ------------------------------------------------

    grouped_entities = defaultdict(list)

    for entity in entities:

        value = extract_entity_value(entity)

        if value:

            grouped_entities[value].append(
                entity
            )

    # ------------------------------------------------
    # CREATE INITIAL CLUSTERS
    # ------------------------------------------------

    for value, group in grouped_entities.items():

        cluster_id = generate_master_id()

        clusters[cluster_id] = set()

        for g in group:

            entity_id = (
                g.get("temp_id")
                or g.get("id")
            )

            clusters[cluster_id].add(
                entity_id
            )

            entity_to_cluster[
                entity_id
            ] = cluster_id

    # ------------------------------------------------
    # RELATION-AWARE ENTITY FUSION
    # ------------------------------------------------

    identity_relations = [
        "USES_PHONE",
        "USES_EMAIL",
        "OWNS_ACCOUNT",
        "USES_DEVICE"
    ]

    for relation in relations:

        relation_type = relation.get(
            "relation"
        )

        if relation_type not in identity_relations:
            continue

        source = relation["source"]
        target = relation["target"]

        source_cluster = (
            entity_to_cluster.get(source)
        )

        target_cluster = (
            entity_to_cluster.get(target)
        )

        # ------------------------------------------------
        # BOTH EXIST → MERGE
        # ------------------------------------------------

        if (
            source_cluster
            and target_cluster
            and source_cluster != target_cluster
        ):

            merge_clusters(
                source_cluster,
                target_cluster,
                clusters
            )

            # Update mappings
            for entity_id in clusters[
                source_cluster
            ]:

                entity_to_cluster[
                    entity_id
                ] = source_cluster

        # ------------------------------------------------
        # ONLY SOURCE EXISTS
        # ------------------------------------------------

        elif source_cluster and not target_cluster:

            clusters[source_cluster].add(
                target
            )

            entity_to_cluster[
                target
            ] = source_cluster

        # ------------------------------------------------
        # ONLY TARGET EXISTS
        # ------------------------------------------------

        elif target_cluster and not source_cluster:

            clusters[target_cluster].add(
                source
            )

            entity_to_cluster[
                source
            ] = target_cluster

        # ------------------------------------------------
        # NEITHER EXISTS
        # ------------------------------------------------

        else:

            new_cluster = generate_master_id()

            clusters[new_cluster] = {
                source,
                target
            }

            entity_to_cluster[
                source
            ] = new_cluster

            entity_to_cluster[
                target
            ] = new_cluster

    # ------------------------------------------------
    # FUZZY PERSON MERGE
    # ------------------------------------------------

    fuzzy_merge_persons(clusters, entity_lookup, entity_to_cluster)

    # ------------------------------------------------
    # SINGLETON CLUSTERS FOR UNCLUSTERED RELATION IDs
    # Any source/target that never entered a cluster
    # (no entity definition + not an identity relation
    # endpoint) still needs a master mapping.
    # ------------------------------------------------

    for relation in relations:

        for entity_id in [
            relation.get("source"),
            relation.get("target")
        ]:

            if entity_id and entity_id not in entity_to_cluster:

                new_cluster = generate_master_id()

                clusters[new_cluster] = {entity_id}

                entity_to_cluster[entity_id] = new_cluster

    # ------------------------------------------------
    # CREATE MASTER ENTITIES
    # ------------------------------------------------

    master_entities = []

    resolved_mapping = {}

    for cluster_id, entity_ids in clusters.items():

        cluster_entities = []

        entity_types = set()

        resolved_values = []

        for entity_id in entity_ids:

            # Always map this ID to the master cluster,
            # even if the entity definition is missing
            resolved_mapping[entity_id] = cluster_id

            entity = entity_lookup.get(
                entity_id
            )

            if not entity:
                continue

            cluster_entities.append(
                entity
            )

            entity_types.add(
                entity.get("type")
            )

            value = extract_entity_value(
                entity
            )

            if value:
                resolved_values.append(
                    value
                )

        # ------------------------------------------------
        # DETERMINE MASTER TYPE
        # ------------------------------------------------

        # Geographic keywords that indicate a PLACE, not a PERSON
        _GEO_KEYWORDS = {
            "station", "bridge", "road", "street", "crossing",
            "bypass", "highway", "expressway", "airport", "junction",
            "lane", "park", "market", "ghat", "lake", "tower",
            "maidan", "chowk", "nagar", "colony", "sector",
            "approach", "flyover", "metro", "terminal", "port",
        }

        if "PERSON" in entity_types or "SOCIAL_HANDLE" in entity_types:

            master_type = "PERSON"

            # Post-classification fix: if entity has BOTH PERSON and
            # LOCATION types, check resolved values for geographic
            # keywords.  If found, this is a place misclassified by
            # spaCy NER, so override to PLACE.
            if "LOCATION" in entity_types:
                all_words = " ".join(resolved_values).lower().split()
                if any(kw in all_words for kw in _GEO_KEYWORDS):
                    master_type = "PLACE"
                    # Remove PERSON from entity_types since it was a
                    # misclassification
                    entity_types.discard("PERSON")

        elif "LOCATION" in entity_types:

            master_type = "PLACE"

        elif (
            "CELL_TOWER" in entity_types
            or "CAMERA" in entity_types
            or "PLATFORM" in entity_types
        ):

            master_type = "INFRASTRUCTURE"

        else:

            master_type = "ENTITY"

        # ------------------------------------------------
        # BUILD MASTER ENTITY
        # ------------------------------------------------

        master_entity = {
            "master_id": cluster_id,
            "master_type": master_type,
            "entity_types": list(
                entity_types
            ),
            "resolved_values": list(
                set(resolved_values)
            ),
            "source_entities": list(
                entity_ids
            )
        }

        master_entities.append(
            master_entity
        )

    # ------------------------------------------------
    # OUTPUT
    # ------------------------------------------------

    return {
        "resolved_mapping": resolved_mapping,
        "master_entities": master_entities
    }
