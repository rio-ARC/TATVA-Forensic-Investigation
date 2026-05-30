"""
social_preprocessor.py — Parses social media post JSON arrays into the
Tatva standard {entities, relations} graph output.
"""

import json
from pathlib import Path

from .communication_utils import (
    extract_entities_from_text,
    make_entity,
    make_relation,
    normalize_timestamp,
)

# Required fields every post must have to be considered valid
_REQUIRED_FIELDS = {"post_id", "platform", "author_handle", "content", "timestamp"}


# ---------------------------------------------------------------------------
# 1. Post loader / validator
# ---------------------------------------------------------------------------

def load_posts(filepath: str) -> list:
    """Load and validate a JSON array of social posts; skip malformed entries."""
    raw = Path(filepath).read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[social_preprocessor] JSON parse error in {filepath}: {exc}")
        return []

    if not isinstance(data, list):
        print(f"[social_preprocessor] Expected a JSON array in {filepath}.")
        return []

    valid = []
    for i, post in enumerate(data):
        missing = _REQUIRED_FIELDS - set(post.keys())
        if missing:
            print(
                f"[social_preprocessor] Skipping post at index {i} "
                f"— missing fields: {missing}"
            )
            continue
        valid.append(post)

    return valid


# ---------------------------------------------------------------------------
# 2. Author entity builder
# ---------------------------------------------------------------------------

def build_author_entity(post: dict, source_file: str) -> dict:
    """Create a SOCIAL_HANDLE entity for the post author."""
    return make_entity(
        entity_type="SOCIAL_HANDLE",
        attributes={
            "handle":   post["author_handle"],
            "name":     post.get("author_name") or "",
            "platform": post["platform"],
        },
        confidence=0.90,
        source=source_file,
    )


# ---------------------------------------------------------------------------
# 3. Platform entity builder
# ---------------------------------------------------------------------------

def build_platform_entity(platform_name: str, source_file: str) -> dict:
    """Create a PLATFORM entity representing a social network."""
    return make_entity(
        entity_type="PLATFORM",
        attributes={"name": platform_name},
        confidence=1.0,
        source=source_file,
    )


# ---------------------------------------------------------------------------
# 4. POSTED_ON relation builder
# ---------------------------------------------------------------------------

def build_posted_on_relation(author_entity: dict, platform_entity: dict,
                             post: dict, source_file: str) -> dict:
    """Build a POSTED_ON relation from a SOCIAL_HANDLE to a PLATFORM entity."""
    return make_relation(
        source_id=author_entity["temp_id"],
        target_id=platform_entity["temp_id"],
        relation="POSTED_ON",
        attributes={
            "post_id":  post["post_id"],
            "content":  post["content"],
            "hashtags": post.get("hashtags", []),
        },
        timestamp=normalize_timestamp(post["timestamp"]),
        confidence=0.95,
        provenance=f"{source_file}:post_{post['post_id']}",
    )


# ---------------------------------------------------------------------------
# 5. Mention relations builder
# ---------------------------------------------------------------------------

def build_mention_relations(author_entity: dict, post: dict,
                            all_handle_entities: dict,
                            source_file: str) -> list:
    """Build MENTIONED_USER relations for every @handle listed in post['mentions']."""
    relations = []
    new_entities = []

    for handle in post.get("mentions", []):
        handle = handle.strip()
        if not handle:
            continue

        if handle in all_handle_entities:
            target_ent = all_handle_entities[handle]
        else:
            # Create a stub entity for the mentioned handle
            target_ent = make_entity(
                entity_type="SOCIAL_HANDLE",
                attributes={
                    "handle":   handle,
                    "name":     "",
                    "platform": post["platform"],
                },
                confidence=0.85,
                source=source_file,
            )
            all_handle_entities[handle] = target_ent
            new_entities.append(target_ent)

        rel = make_relation(
            source_id=author_entity["temp_id"],
            target_id=target_ent["temp_id"],
            relation="MENTIONED_USER",
            attributes={"post_id": post["post_id"]},
            timestamp=normalize_timestamp(post["timestamp"]),
            confidence=0.85,
            provenance=f"{source_file}:post_{post['post_id']}",
        )
        relations.append(rel)

    return relations, new_entities


# ---------------------------------------------------------------------------
# 6. Main pipeline entry point
# ---------------------------------------------------------------------------

def preprocess_social(filepath: str) -> dict:
    """Orchestrate full social-media preprocessing pipeline; return {entities, relations}."""
    source_file = Path(filepath).name
    posts = load_posts(filepath)

    entities  = []
    relations = []

    # -----------------------------------------------------------------------
    # First pass — build all author entities, index by handle
    # -----------------------------------------------------------------------
    handle_entities = {}   # handle_str -> entity dict

    for post in posts:
        handle = post["author_handle"]
        if handle not in handle_entities:
            ent = build_author_entity(post, source_file)
            handle_entities[handle] = ent
            entities.append(ent)

    # -----------------------------------------------------------------------
    # Build platform entities — one per unique platform string
    # -----------------------------------------------------------------------
    platform_entities = {}   # platform_name -> entity dict

    for post in posts:
        pname = post["platform"]
        if pname not in platform_entities:
            ent = build_platform_entity(pname, source_file)
            platform_entities[pname] = ent
            entities.append(ent)

    # -----------------------------------------------------------------------
    # Second pass — relations and inline entity extraction
    # -----------------------------------------------------------------------
    for post in posts:
        author_ent   = handle_entities[post["author_handle"]]
        platform_ent = platform_entities[post["platform"]]

        # POSTED_ON relation
        relations.append(
            build_posted_on_relation(author_ent, platform_ent, post, source_file)
        )

        # MENTIONED_USER relations for explicit @mentions
        mention_rels, new_ents = build_mention_relations(
            author_ent, post, handle_entities, source_file
        )
        entities.extend(new_ents)
        relations.extend(mention_rels)

        # Inline entity extraction from post content
        inline_entities = extract_entities_from_text(post["content"], source_file)
        for ie in inline_entities:
            entities.append(ie)
            relations.append(make_relation(
                source_id=author_ent["temp_id"],
                target_id=ie["temp_id"],
                relation="MENTIONED",
                attributes={"post_id": post["post_id"]},
                timestamp=normalize_timestamp(post["timestamp"]),
                confidence=0.70,
                provenance=f"{source_file}:post_{post['post_id']}",
            ))

    return {"entities": entities, "relations": relations}


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    result = preprocess_social(
        sys.argv[1] if len(sys.argv) > 1 else "sample_data/sample_social.json"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
