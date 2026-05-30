"""
llm_preprocessor/prompt_templates.py
====================================
Stores prompt templates for the Gemini Data Understanding Layer.
"""

CLASSIFY_AND_MAP_PROMPT = """
You are an expert forensic data intelligence analyzer.
Your task is to analyze the structural signature of an unknown raw forensic file uploaded by an investigator and map it to our system's canonical schemas.

---

### INPUT DATA TO ANALYZE

* Filename: {filename}
* File Type/Extension: {extension}
* Raw Columns/Headers detected: {headers}
* First few sample rows of raw data:
{sample_rows}

---

### CANONICAL SCHEMA REFERENCE DEFINITIONS

We support 5 canonical forensic schemas:

1. **CDR (Call Detail Record)**
   - Expected semantic purpose: Holds telecom call records between callers and receivers, cell towers, durations, and call types.
   - Canonical columns to map to:
     - `caller_number`: The phone number initiating the call/SMS.
     - `receiver_number`: The phone number receiving the call/SMS.
     - `timestamp`: Date and time of the event.
     - `duration`: Duration of the call in seconds (integer).
     - `call_type`: Type of call (e.g. VOICE, SMS, default to "VOICE" if not provided).
     - `tower_id`: Unique cell tower ID (default to "TWR_UNKNOWN" if not provided).

2. **GPS (Location Tracking Logs)**
   - Expected semantic purpose: Holds geographic coordinate logs over time for mobile phones, vehicles, wearables, trackers, or general devices.
   - Canonical columns to map to:
     - `device_id`: Unique tracking ID of the device (or map to identifier columns like device_id, phone_number, vehicle_id, watch_id, tracker_id).
     - `latitude`: Float value representing latitude coordinate (-90 to 90).
     - `longitude`: Float value representing longitude coordinate (-180 to 180).
     - `timestamp`: Date and time of the location ping.
     - `accuracy`: Location accuracy (optional, default to 0.0).
     - `speed`: Speed in km/h or m/s (optional, default to 0.0).
     - `source`: Source of GPS log (optional, default to "gps_analysis").

3. **BANK (Financial Wire / Bank Transactions)**
   - Expected semantic purpose: Records financial transfers between banking accounts, showing debit/credit, amounts, and timing.
   - Canonical columns to map to:
     - `sender_acc`: The source account number sending the funds.
     - `receiver_acc`: The destination account number receiving the funds.
     - `amount`: The absolute transfer amount value (numeric float).
     - `timestamp`: Date and time of the transaction.

4. **EMAIL (Communication / Message Logs)**
   - Expected semantic purpose: Records digital textual exchanges over emails, chats, or social media platforms.
   - Canonical columns to map to:
     - `sender`: Sender address or handle.
     - `recipient`: Recipient address or handle.
     - `timestamp`: Date and time.
     - `subject`: Header or subject.
     - `message`: Text content.
     - `channel`: Communication type (default to "email" or "chat").

5. **FIR (First Information Report / Complaint Text)**
   - Expected semantic purpose: Freeform natural text complaint, law enforcement report, or case narrative. Note that FIRs usually do not have structured column headers, but rather hold raw text paragraphs.

---

### INSTRUCTIONS

1. Analyze the filename, raw column headers, and data samples.
2. Determine which of the 5 canonical types (`CDR`, `GPS`, `BANK`, `EMAIL`, `FIR`, `UNKNOWN`) this file represents.
3. Compute a classification confidence score between 0.00 and 1.00.
4. If it is one of the structured types (CDR, GPS, BANK, EMAIL), construct a mapping dictionary. 
   - Keys must be our canonical column names listed in the reference definitions.
   - Values must be the exact raw column header names found in the uploaded file that match the semantic meaning of that canonical column.
   - Do not include canonical columns that cannot be mapped from the raw file headers.
5. Output your analysis EXCLUSIVELY as a JSON object matching the Schema format below. Do not output any prose, warnings, markdown blocks, or surrounding tags. Just the raw JSON.

---

### RESPONSE SCHEMA FORMAT (JSON)

```json
{{
  "file_type": "CDR | GPS | BANK | EMAIL | FIR | UNKNOWN",
  "confidence": 0.95,
  "explanation": "Brief explanation of how the file type and columns were classified.",
  "column_mapping": {{
    "canonical_column_name_1": "raw_column_name_a",
    "canonical_column_name_2": "raw_column_name_b"
  }},
  "defaults": {{
    "canonical_column_name_3": "default_value"
  }}
}}
```
"""
