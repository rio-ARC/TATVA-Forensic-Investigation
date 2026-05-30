# Risk Intelligence Engine - Rules Documentation

This document describes the 10 risk assessment rules, scoring formulas, and validation logic implemented inside the **Risk Intelligence Engine** (`backend/analysis/rule_validation/`).

---

## 1. Risk Contribution Formula

To ensure explainable and realistic risk profiling, raw scores are weighted based on the reliability of the data source and the preprocessor confidence:

$$\text{Risk Contribution} = \text{Rule Weight} \times \text{Evidence Confidence} \times \text{Source Reliability} \times \text{Time Decay}$$

### Source Reliability Weights
Different evidence channels have varying levels of reliability:
- **1.0** — Bank Transactions, CDR (Call Detail Record) logs, Telecom towers, Mobile GPS, Asset/Vehicle trackers (hard device/sensor/financial logs).
- **0.9** — Official FIR documents, investigator annotations.
- **0.8** — Chat conversations (WhatsApp, Telegram), social media posts, emails, vehicle camera detections (semi-structured or text-extracted signals).

### Time Decay Mechanism
Evidence value decays exponentially as it ages relative to the latest transaction/event timestamp ($T_{max}$) in the graph:

$$\text{Time Decay} = \exp(-\lambda \times \text{age in days})$$

Where $\lambda = 0.05$ (equivalent to half-life of $\approx 14$ days, so evidence decays moderately over weeks, highlighting fresh operations while retaining history).

---

## 2. Rule Catalogue

### Rule 1: Excessive Calling (COMM_EXCESSIVE_CALLING)
- **Description**: A person makes > 50 outgoing calls in a single day.
- **Weight**: `+5`
- **Implementation**: Filters `CALLED` relationships where the target node is a phone call or communication entity, grouped by date.

### Rule 2: Call Burst (COMM_CALL_BURST)
- **Description**: 10+ calls (incoming or outgoing) within a sliding 15-minute window for a single person.
- **Weight**: `+8`
- **Implementation**: Evaluates communication timestamps chronologically per person and flags bursts.

### Rule 3: Hub Communication (COMM_HUB)
- **Description**: Person is connected to > 20 unique phone number/communication target entities.
- **Weight**: `+10`
- **Implementation**: Counts unique targets of `CALLED` or `MESSAGED` relations.

### Rule 4: Mule Pattern (FIN_MULE_PATTERN)
- **Description**: Inbound transaction immediately followed by outbound transaction.
- **Weight**: `+20`
- **Implementation**: Detects if an entity receives funds via `TRANSFERRED_TO` and then transfers funds outbound to another account within a 30-minute window.

### Rule 5: Smurfing (FIN_SMURFING)
- **Description**: 3+ outbound transactions under the AML reporting threshold (10,000 INR) in a sliding 30-minute window.
- **Weight**: `+15`
- **Implementation**: Groups outbound transfers, flags if multiple low-amount transfers are sent within the window.

### Rule 6: High Velocity (FIN_HIGH_VELOCITY)
- **Description**: 10+ financial transactions (inbound or outbound) in a sliding 30-minute window.
- **Weight**: `+10`
- **Implementation**: Detects rapid transaction chains regardless of individual amounts.

### Rule 7: Suspicious Co-location (GPS_SUSPICIOUS_COLOCATION)
- **Description**: Two entities located at the same place at the same time (within ±15 minutes), where one is a known suspect.
- **Weight**: `+12`
- **Implementation**: Cross-references GPS logs, cell tower connections, and tracking logs. Known suspect is resolved as `Rahul Sen` (named in the FIR).

### Rule 8: Frequent Visits (GPS_FREQUENT_VISITS)
- **Description**: Repeated visits (3+) by a person to the same location.
- **Weight**: `+8`
- **Implementation**: Counts distinct timestamps of `LOCATED_AT` or `MOVED_TO` relations targeting the same place.

### Rule 9: Deletion Language (COMM_DELETION_LANGUAGE)
- **Description**: Messaging or emails containing instruction to delete messages or destroy evidence.
- **Weight**: `+10`
- **Implementation**: Scans for `delete_instruction` or `has_urgency` flags in message metadata attributes or scans content for keywords ("delete", "wipe", "clear").

### Rule 10: Money Request (COMM_MONEY_REQUEST)
- **Description**: Messages containing transaction-related terminology (e.g. transfer, withdraw, cash).
- **Weight**: `+15`
- **Implementation**: Scans for `has_money_ref` in chat attributes or keywords ("transfer", "withdraw", "account", "cash").

---

## 3. Score Normalization & Classification
To obtain the final explainable risk score (0-100 scale), raw scores are normalized against a saturation cap of `60.0` points:

$$\text{Risk Score} = \min\left(100.0, \frac{\text{Sum of Contributions}}{60.0} \times 100.0\right)$$

### Risk Level Ranges
- **Risk Score >= 80** → CRITICAL RISK (High Interest)
- **Risk Score >= 50** → HIGH RISK
- **Risk Score >= 25** → MEDIUM RISK
- **Risk Score < 25** → LOW RISK
