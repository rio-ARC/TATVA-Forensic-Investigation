"""
communication_utils.py — Shared utility functions for Chats_Social preprocessors.

This module owns the spaCy model load and all shared factory functions.
No other file in this package should load spaCy directly.
"""

import re
import uuid
from dateutil import parser as dateutil_parser

import spacy

# ---------------------------------------------------------------------------
# Module-level cache — load once, reuse across all importers
# ---------------------------------------------------------------------------

_NLP_MODEL = None


# ---------------------------------------------------------------------------
# 1. NLP model loader
# ---------------------------------------------------------------------------

def load_nlp_model() -> spacy.Language:
    """Load en_core_web_lg once and cache it at module level; return the model."""
    global _NLP_MODEL
    if _NLP_MODEL is None:
        _NLP_MODEL = spacy.load("en_core_web_sm")
    return _NLP_MODEL


# ---------------------------------------------------------------------------
# 2. Inline entity extractor
# ---------------------------------------------------------------------------

# Regex: Indian mobile number — 10 digits, optional +91 or leading 0 prefix
_PHONE_RE = re.compile(r'(?:\+91|0)?[6-9]\d{9}')

# Regex: email address
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

# spaCy label → Tatva entity type mapping
_LABEL_MAP = {
    "PERSON": "PERSON",
    "GPE":    "LOCATION",
    "LOC":    "LOCATION",
    "ORG":    "PERSON",   # treat organisations as actors for forensics
}

# Labels we explicitly skip
_SKIP_LABELS = {"CARDINAL", "QUANTITY", "ORDINAL", "PERCENT", "MONEY",
                "TIME", "DATE", "PRODUCT", "EVENT", "WORK_OF_ART",
                "LAW", "LANGUAGE", "FAC", "NORP"}


def extract_entities_from_text(text: str, source_file: str) -> list:
    """Run spaCy NER and regex on text; return a list of entity dicts."""
    nlp = load_nlp_model()
    doc = nlp(text)
    results = []
    seen_texts = set()   # deduplicate within this call

    # --- spaCy NER ---
    for ent in doc.ents:
        if ent.label_ in _SKIP_LABELS:
            continue
        tatva_type = _LABEL_MAP.get(ent.label_)
        if tatva_type is None:
            continue
        key = (tatva_type, ent.text.strip())
        if key in seen_texts:
            continue
        seen_texts.add(key)
        attr_key = "name" if tatva_type in ("PERSON", "LOCATION") else "value"
        results.append(make_entity(
            entity_type=tatva_type,
            attributes={attr_key: ent.text.strip()},
            confidence=0.80,
            source=source_file,
        ))

    # --- regex: phone numbers ---
    for match in _PHONE_RE.finditer(text):
        number = re.sub(r'\D', '', match.group())
        if len(number) > 10:
            number = number[-10:]
        key = ("PHONE_NUMBER", number)
        if key in seen_texts:
            continue
        seen_texts.add(key)
        results.append(make_entity(
            entity_type="PHONE_NUMBER",
            attributes={"number": number},
            confidence=0.95,
            source=source_file,
        ))

    # --- regex: email addresses ---
    for match in _EMAIL_RE.finditer(text):
        addr = match.group().lower()
        key = ("EMAIL_ADDRESS", addr)
        if key in seen_texts:
            continue
        seen_texts.add(key)
        results.append(make_entity(
            entity_type="EMAIL_ADDRESS",
            attributes={"address": addr},
            confidence=0.97,
            source=source_file,
        ))

    return results


# ---------------------------------------------------------------------------
# 3. Entity factory
# ---------------------------------------------------------------------------

def make_entity(entity_type: str, attributes: dict, confidence: float, source: str) -> dict:
    """Build a single entity dict with a generated temp_id matching the output contract."""
    temp_id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
    return {
        "temp_id": temp_id,
        "type": entity_type,
        "attributes": attributes,
        "confidence": confidence,
        "source": source,
    }


# ---------------------------------------------------------------------------
# 4. Relation factory
# ---------------------------------------------------------------------------

def make_relation(source_id: str, target_id: str, relation: str, attributes: dict, timestamp, confidence: float, provenance: str) -> dict:
    """Build a single relation dict matching the output contract."""
    return {
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "attributes": attributes,
        "timestamp": timestamp,
        "confidence": confidence,
        "provenance": provenance,
    }


# ---------------------------------------------------------------------------
# 5. Timestamp normaliser
# ---------------------------------------------------------------------------

def normalize_timestamp(raw: str):
    """Parse any timestamp string to ISO 8601; return None if parsing fails."""
    if not raw:
        return None
    try:
        return dateutil_parser.parse(raw).isoformat()
    except Exception:
        return None
