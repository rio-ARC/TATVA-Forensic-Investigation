"""
Pre-populate the geo_cache.json by resolving ALL unique GPS coordinates
found in the preprocessed graph data via Nominatim API.

Run this ONCE before running main.py so that the entity resolution
can use cached place names instead of hitting the API mid-pipeline.
"""

import json
import time
import os
import requests

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output/geo_cache.json")
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output/all_preprocessed_graphs.json")


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def resolve(lat, lon):
    """Call Nominatim reverse geocoding and return a place name string."""
    try:
        resp = requests.get(
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
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        address = data.get("address", {})
        road   = address.get("road")
        suburb = address.get("suburb") or address.get("neighbourhood")
        city   = address.get("city") or address.get("town") or address.get("county")

        parts = [p for p in [road, suburb, city] if p]
        if parts:
            return ", ".join(parts).lower()

        display = data.get("display_name")
        if display:
            return ", ".join(display.split(",")[:3]).strip().lower()

    except Exception as e:
        print(f"    [ERROR] API call failed: {e}")

    return None


def main():
    # Collect unique coordinates from preprocessed graph entities
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] {DATA_FILE} not found. Run preprocessed_outputs.py first.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    coords = set()
    for entity in data.get("entities", []):
        if entity.get("type") == "LOCATION":
            attrs = entity.get("attributes", {})
            lat = attrs.get("latitude")
            lon = attrs.get("longitude")
            if lat is not None and lon is not None:
                coords.add((round(float(lat), 5), round(float(lon), 5)))

    print(f"[INFO] Found {len(coords)} unique coordinate pairs to resolve.\n")

    cache = load_cache()
    resolved_count = 0
    skipped_count = 0

    for lat, lon in sorted(coords):
        key = f"{lat},{lon}"
        if key in cache and not cache[key].startswith("location near"):
            print(f"  [CACHED] {key} => {cache[key]}")
            skipped_count += 1
            continue

        print(f"  [RESOLVING] {key} ...", end=" ", flush=True)
        name = resolve(lat, lon)

        if name:
            cache[key] = name
            print(f"=> {name}")
            resolved_count += 1
        else:
            fallback = f"location near {lat:.4f}n, {lon:.4f}e"
            cache[key] = fallback
            print(f"=> {fallback} (fallback)")

        save_cache(cache)
        time.sleep(1.1)  # Comply with Nominatim 1 req/sec policy

    print(f"\n[DONE] Resolved: {resolved_count}, Already cached: {skipped_count}")
    print(f"[INFO] Cache saved to: {CACHE_FILE}")


if __name__ == "__main__":
    main()
