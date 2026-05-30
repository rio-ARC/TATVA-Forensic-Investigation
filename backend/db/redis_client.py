"""
Upstash Redis client for TATVA Forensic Investigation.

Provides a caching layer for:
  - Geo-location lookups (replacing file-based geo_cache.json)
  - Computed graph insights (suspects, alerts, timeline, summary)
  - API response caching with TTL
  - Rate-limit tracking for Nominatim API
"""
import os
import json
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")


class RedisClient:
    """
    Upstash Redis REST client for caching.

    All values are JSON-serialised before storage and deserialised on read,
    so you can cache dicts, lists, strings, and numbers transparently.
    """

    def __init__(self, url: str = None, token: str = None):
        self.url = url or UPSTASH_URL
        self.token = token or UPSTASH_TOKEN
        self.redis = None
        self._connect()

    def _connect(self):
        if not self.url or not self.token:
            print("[Redis] WARNING: Upstash credentials not set in .env. Cache disabled.")
            return

        try:
            from upstash_redis import Redis
            self.redis = Redis(url=self.url, token=self.token)
            # Quick connectivity check
            self.redis.ping()
            print("[Redis] Connected to Upstash successfully.")
        except Exception as e:
            print(f"[Redis] Connection failed: {e}")
            self.redis = None

    @property
    def connected(self) -> bool:
        return self.redis is not None

    # ── Core Operations ───────────────────────────────────────

    def set(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Store a value. Optionally set a TTL (expiry in seconds)."""
        if not self.redis:
            return False
        try:
            serialised = json.dumps(value)
            if ttl_seconds:
                self.redis.setex(key, ttl_seconds, serialised)
            else:
                self.redis.set(key, serialised)
            return True
        except Exception as e:
            print(f"[Redis] SET error for '{key}': {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key. Returns None if not found or not connected."""
        if not self.redis:
            return None
        try:
            raw = self.redis.get(key)
            if raw is None:
                return None
            # Upstash REST client may return the value already decoded
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return raw
            return raw
        except Exception as e:
            print(f"[Redis] GET error for '{key}': {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key."""
        if not self.redis:
            return False
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"[Redis] DELETE error for '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self.redis:
            return False
        try:
            return bool(self.redis.exists(key))
        except Exception:
            return False

    def keys(self, pattern: str = "*") -> list:
        """List keys matching a pattern."""
        if not self.redis:
            return []
        try:
            result = self.redis.keys(pattern)
            return result if result else []
        except Exception as e:
            print(f"[Redis] KEYS error: {e}")
            return []

    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count deleted."""
        if not self.redis:
            return 0
        matching = self.keys(pattern)
        count = 0
        for key in matching:
            if self.delete(key):
                count += 1
        return count

    # ── Geo-Cache Operations ──────────────────────────────────

    def set_geo(self, lat: float, lon: float, place_name: str) -> bool:
        """Cache a reverse-geocoded place name."""
        key = f"geo:{lat:.6f},{lon:.6f}"
        return self.set(key, place_name)

    def get_geo(self, lat: float, lon: float) -> Optional[str]:
        """Look up a cached place name by coordinates."""
        key = f"geo:{lat:.6f},{lon:.6f}"
        return self.get(key)

    def bulk_set_geo(self, geo_dict: dict) -> int:
        """Bulk-load geo cache entries from a dict like {"lat,lon": "place name"}."""
        count = 0
        for coord_str, place_name in geo_dict.items():
            try:
                parts = coord_str.split(",")
                lat, lon = float(parts[0]), float(parts[1])
                if self.set_geo(lat, lon, place_name):
                    count += 1
            except (ValueError, IndexError):
                continue
        return count

    # ── Insight Cache Operations ──────────────────────────────

    def cache_insights(self, insight_type: str, data: Any, ttl: int = 3600) -> bool:
        """Cache computed insights with 1-hour default TTL."""
        key = f"insight:{insight_type}"
        return self.set(key, data, ttl_seconds=ttl)

    def get_cached_insights(self, insight_type: str) -> Optional[Any]:
        """Retrieve cached insights."""
        key = f"insight:{insight_type}"
        return self.get(key)

    def invalidate_insights(self) -> int:
        """Clear all cached insights (e.g., after new data import)."""
        return self.flush_pattern("insight:*")

    # ── API Response Cache ────────────────────────────────────

    def cache_api_response(self, endpoint: str, data: Any, ttl: int = 300) -> bool:
        """Cache an API response with 5-minute default TTL."""
        key = f"api:{endpoint}"
        return self.set(key, data, ttl_seconds=ttl)

    def get_cached_api_response(self, endpoint: str) -> Optional[Any]:
        """Get a cached API response."""
        key = f"api:{endpoint}"
        return self.get(key)

    # ── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return basic cache statistics."""
        if not self.redis:
            return {"connected": False}
        try:
            geo_keys = len(self.keys("geo:*"))
            insight_keys = len(self.keys("insight:*"))
            api_keys = len(self.keys("api:*"))
            all_keys = len(self.keys("*"))
            return {
                "connected": True,
                "total_keys": all_keys,
                "geo_cache_entries": geo_keys,
                "insight_cache_entries": insight_keys,
                "api_cache_entries": api_keys,
            }
        except Exception:
            return {"connected": True, "error": "Could not fetch stats"}


# ── Standalone Test ───────────────────────────────────────────
if __name__ == "__main__":
    client = RedisClient()
    if client.connected:
        # Test basic operations
        print("\n[Redis] Testing SET/GET...")
        client.set("test:hello", {"message": "TATVA Redis is alive!", "ts": "2026-05-30"})
        result = client.get("test:hello")
        print(f"  -> GET test:hello = {result}")

        # Test geo cache
        print("\n[Redis] Testing Geo-Cache...")
        client.set_geo(28.6139, 77.2090, "New Delhi, India")
        place = client.get_geo(28.6139, 77.2090)
        print(f"  -> geo lookup (28.6139, 77.2090) = {place}")

        # Cleanup test keys
        client.delete("test:hello")

        # Stats
        print(f"\n[Redis] Stats: {client.get_stats()}")
    else:
        print("[Redis] Not connected — skipping tests.")
