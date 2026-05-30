# Tatva Chats_Social Preprocessor Module

## Overview
The **Chats_Social** preprocessor extracts structured forensic entities and relationships from three data sources:
- **Chat transcripts** (`chat_preprocessor.py`)
- **Emails** (`email_preprocessor.py`)
- **Social media JSON** (`social_preprocessor.py`)

All processors share a common utility (`communication_utils.py`) that provides:
- A singleton **spaCy** language model
- Factory helpers to create **entity** and **relation** dictionaries adhering to the platform contract
- Regex‑based extractors for phone numbers, email addresses, and social handles

## Files & Functions
| File | Primary Functions |
|------|-------------------|
| `communication_utils.py` | `get_spacy_model()`, `create_entity()`, `create_relation()`, `extract_phone_numbers()`, `extract_emails()`, `extract_social_handles()` |
| `chat_preprocessor.py` | `process_chat_file(path: Path) → dict` |
| `email_preprocessor.py` | `process_email_file(path: Path) → dict` |
| `social_preprocessor.py` | `process_social_json(path: Path) → dict` |
| `sample_data/sample_chat.txt` | Example chat transcript used for quick testing |
| `sample_data/sample_email.txt` | Example raw email used for quick testing |
| `sample_data/sample_social.json` | Example social media payload containing three forensic‑relevant posts |
| `README.md` | This documentation |

## Processing Flow
1. **Load spaCy model** – `communication_utils.get_spacy_model()` lazily loads the English model once per process.
2. **Read input** – Each processor reads its respective file format (plain‑text chat, raw email, or JSON social payload).
3. **Entity extraction** –
   - Use spaCy NER for PERSON, ORG, GPE, etc.
   - Apply regex helpers for PHONE_NUMBER, EMAIL_ADDRESS, SOCIAL_HANDLE, PLATFORM.
4. **Relation building** – Simple heuristic relations are added (e.g., `MENTIONS`, `SENT_FROM`).
5. **Wrap output** – Each processor returns a dict matching the platform contract:
```json
{
  "entities": [ { "temp_id": "PERSON_1a2b3c4d", "type": "PERSON", "attributes": {…}, "confidence": 0.96, "source": "chat", "provenance": { "file": "sample_chat.txt", "line": 12 } } ],
  "relations": [ { "source_id": "PERSON_…", "target_id": "PHONE_NUMBER_…", "type": "HAS_CONTACT", "confidence": 0.88 } ]
}
```

## Output Shape
All processors output a **single JSON‑serialisable dictionary** with two top‑level keys:
- `entities`: list of entity objects (`temp_id`, `type`, `attributes`, `confidence`, `source`, `provenance`).
- `relations`: list of relation objects (`source_id`, `target_id`, `type`, `confidence`).

The schema is validated by downstream modules for deterministic graph construction.

## Running the Preprocessors
```bash
# From the project root (TATVA)
python -m backend.preprocessor.Chats_Social.chat_preprocessor
python -m backend.preprocessor.Chats_Social.email_preprocessor
python -m backend.preprocessor.Chats_Social.social_preprocessor
```
Each script defaults to the corresponding sample file in `sample_data/`.  Pass a custom file path as the first positional argument if desired (e.g., `python -m backend.preprocessor.Chats_Social.chat_preprocessor my_chat.txt`).

