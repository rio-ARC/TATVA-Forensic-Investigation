"""
email_preprocessor.py — Parses raw .eml or plain-text email files into the
Tatva standard {entities, relations} graph output.
"""

import re
import json
from email import parser as email_parser
from email import policy
from pathlib import Path

from .communication_utils import (
    extract_entities_from_text,
    make_entity,
    make_relation,
    normalize_timestamp,
)

# ---------------------------------------------------------------------------
# Regex patterns for plain-text email header fallback
# ---------------------------------------------------------------------------

_HDR_FROM    = re.compile(r'^From:\s*(.+)$',    re.MULTILINE | re.IGNORECASE)
_HDR_TO      = re.compile(r'^To:\s*(.+)$',      re.MULTILINE | re.IGNORECASE)
_HDR_CC      = re.compile(r'^Cc:\s*(.+)$',      re.MULTILINE | re.IGNORECASE)
_HDR_SUBJECT = re.compile(r'^Subject:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
_HDR_DATE    = re.compile(r'^Date:\s*(.+)$',    re.MULTILINE | re.IGNORECASE)

# Display-name + address: "Name <addr>" or just "addr"
_ADDR_RE = re.compile(
    r'^(?:"?(?P<name>[^"<>]+?)"?\s*)?<?(?P<addr>[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})>?$'
)

# Suspicious signal keyword sets (lowercased)
_OTP_WORDS      = {"otp", "one time password", "verification code"}
_BANK_WORDS     = {"kyc", "your account", "sbi", "bank"}
_ACCOUNT_WORDS  = {"account number", "ifsc", "details"}
_URGENCY_WORDS  = {"immediately", "urgent", "within 24 hours"}
_DELETE_WORDS   = {"delete this", "do not forward"}


# ---------------------------------------------------------------------------
# 1. Email file parser
# ---------------------------------------------------------------------------

def parse_email_file(filepath: str) -> dict:
    """Parse a .eml or plain-text email file; return a normalised header dict."""
    raw = Path(filepath).read_text(encoding="utf-8", errors="replace")

    # Try stdlib email parser first (handles proper .eml structure)
    p = email_parser.Parser(policy=policy.default)
    msg = p.parsestr(raw)

    from_hdr    = msg.get("From",    "")
    to_hdr      = msg.get("To",      "")
    cc_hdr      = msg.get("Cc",      None)
    subject_hdr = msg.get("Subject", "")
    date_hdr    = msg.get("Date",    "")

    # Extract body: prefer plain-text part
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(
                    part.get_content_charset("utf-8"), errors="replace"
                )
                break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(
                msg.get_content_charset("utf-8"), errors="replace"
            )
        else:
            # Payload may already be a string for plain-text files
            raw_payload = msg.get_payload()
            if isinstance(raw_payload, str):
                body = raw_payload

    # If stdlib parser found no useful headers, fall back to regex on raw text
    if not from_hdr and not to_hdr:
        from_hdr    = _match_first(_HDR_FROM,    raw)
        to_hdr      = _match_first(_HDR_TO,      raw)
        cc_hdr      = _match_first(_HDR_CC,      raw)
        subject_hdr = _match_first(_HDR_SUBJECT, raw)
        date_hdr    = _match_first(_HDR_DATE,    raw)
        # Body is everything after the first blank line following headers
        split = re.split(r'\n\s*\n', raw, maxsplit=1)
        body  = split[1].strip() if len(split) > 1 else ""

    subject = subject_hdr.strip() if subject_hdr else ""
    is_reply = subject.lower().startswith(("re:", "re :", "fw:", "fwd:"))

    return {
        "from":     from_hdr.strip()    if from_hdr    else "",
        "to":       to_hdr.strip()      if to_hdr      else "",
        "cc":       cc_hdr.strip()      if cc_hdr      else None,
        "subject":  subject,
        "date":     normalize_timestamp(date_hdr.strip()) if date_hdr else None,
        "body":     body.strip(),
        "is_reply": is_reply,
    }


def _match_first(pattern: re.Pattern, text: str) -> str:
    """Return the first capture group of a regex match, or empty string."""
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# 2. Email address extractor
# ---------------------------------------------------------------------------

def extract_email_address(raw_header: str) -> tuple:
    """Parse 'Name <addr>' or bare address; return (display_name, email_addr)."""
    raw_header = raw_header.strip().strip('"')
    m = _ADDR_RE.match(raw_header)
    if m:
        name = (m.group("name") or "").strip()
        addr = (m.group("addr") or "").strip().lower()
        return (name, addr)
    # Last-resort: try to find an email pattern anywhere in the string
    addr_m = re.search(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', raw_header
    )
    if addr_m:
        addr = addr_m.group().lower()
        name = raw_header.replace(addr_m.group(), "").strip(" <>()\",")
        return (name, addr)
    return ("", raw_header.lower())


# ---------------------------------------------------------------------------
# 3. Email entity builder
# ---------------------------------------------------------------------------

def build_email_entity(display_name: str, email_addr: str,
                       source_file: str) -> dict:
    """Create a PERSON entity carrying both display name and email address."""
    confidence = 0.95 if display_name else 0.85
    return make_entity(
        entity_type="PERSON",
        attributes={"name": display_name, "email": email_addr},
        confidence=confidence,
        source=source_file,
    )


# ---------------------------------------------------------------------------
# 4. Suspicious signal detector
# ---------------------------------------------------------------------------

def detect_suspicious_email_signals(subject: str, body: str) -> dict:
    """Scan subject + body for known forensic red-flag patterns."""
    combined = (subject + " " + body).lower()

    def _any(*phrases):
        return any(p in combined for p in phrases)

    return {
        "requests_otp":          _any("otp", "one time password", "verification code"),
        "impersonates_bank":     _any("kyc", "your account", "sbi", "bank"),
        "requests_account_info": _any("account number", "ifsc", "details"),
        "urgency_language":      _any("immediately", "urgent", "within 24 hours"),
        "delete_instruction":    _any("delete this", "do not forward"),
    }


# ---------------------------------------------------------------------------
# 5. Main pipeline entry point
# ---------------------------------------------------------------------------

def preprocess_email(filepath: str) -> dict:
    """Orchestrate full email preprocessing pipeline; return {entities, relations}."""
    source_file = Path(filepath).name
    parsed = parse_email_file(filepath)

    entities = []
    relations = []

    # --- Build sender entity ---
    from_name, from_addr = extract_email_address(parsed["from"])
    sender_entity = build_email_entity(from_name, from_addr, source_file)
    entities.append(sender_entity)

    # --- Build To recipient(s) ---
    to_entities = []
    for raw_addr in _split_addresses(parsed["to"]):
        name, addr = extract_email_address(raw_addr)
        if addr:
            ent = build_email_entity(name, addr, source_file)
            entities.append(ent)
            to_entities.append(ent)

    # --- Build CC recipient(s) ---
    cc_entities = []
    if parsed["cc"]:
        for raw_addr in _split_addresses(parsed["cc"]):
            name, addr = extract_email_address(raw_addr)
            if addr:
                ent = build_email_entity(name, addr, source_file)
                entities.append(ent)
                cc_entities.append(ent)

    # --- Forensic signals ---
    signals = detect_suspicious_email_signals(parsed["subject"], parsed["body"])

    # --- Build EMAILED relations ---
    all_recipients = to_entities + cc_entities
    for recipient_ent in all_recipients:
        rel = make_relation(
            source_id=sender_entity["temp_id"],
            target_id=recipient_ent["temp_id"],
            relation="EMAILED",
            attributes={
                "subject":          parsed["subject"],
                "is_reply":         parsed["is_reply"],
                "forensic_signals": signals,
            },
            timestamp=parsed["date"],
            confidence=0.97,
            provenance=f"{source_file}:header",
        )
        relations.append(rel)

    # --- Inline entity extraction from body ---
    inline_entities = extract_entities_from_text(parsed["body"], source_file)
    for ie in inline_entities:
        entities.append(ie)
        relations.append(make_relation(
            source_id=sender_entity["temp_id"],
            target_id=ie["temp_id"],
            relation="MENTIONED",
            attributes={"context": "email_body"},
            timestamp=parsed["date"],
            confidence=0.75,
            provenance=f"{source_file}:body",
        ))

    return {"entities": entities, "relations": relations}


def _split_addresses(header_val: str) -> list:
    """Split a comma-separated address header into individual address strings."""
    if not header_val:
        return []
    return [a.strip() for a in header_val.split(",") if a.strip()]


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    result = preprocess_email(
        sys.argv[1] if len(sys.argv) > 1 else "sample_data/sample_email.txt"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
