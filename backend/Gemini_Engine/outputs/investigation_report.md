# FORENSIC INVESTIGATION REPORT

**Date:** 2026-05-31
**Prepared For:** Senior Corporate Security Directors / Law Enforcement
**Prepared By:** Senior Forensic Intelligence Analyst

## Executive Summary

This report synthesizes forensic intelligence from an automated data pipeline concerning suspicious activity observed between May 22, 2026, and May 29, 2026. The investigation centers around a highly coordinated and deliberate money laundering scheme involving multiple individuals, structured financial transactions, and covert communications, primarily executed within a concentrated timeframe on May 22, 2026.

**Key Findings:**
*   **Coordinated Money Laundering:** Primary suspect Rahul Sen initiated a classic "smurfing" operation, fragmenting a significant sum (Rs. 64,400) into seven sub-threshold UPI transfers (each < Rs. 10,000) to various intermediary accounts (ACC2001-ACC8001).
*   **Mule Account Utilization:** These intermediary accounts immediately forwarded the aggregated funds to Rajan Mehta, who then acted as a central "mule," consolidating the total Rs. 64,400 and swiftly transferring it to an external account, "ACC_HAWALA," via NEFT.
*   **Physical & Digital Coordination:** The financial transfers were meticulously coordinated through a series of timed phone calls, group chat messages, and physical rendezvous. Key individuals (Rahul Sen, Vikram Khanna, and an asset tracker/cab) were co-located at "Chatterjee Lane, Bowbazar, Kolkata" prior to and during the initial smurfing transfers, strongly indicating in-person orchestration.
*   **Intent to Conceal:** Explicit instructions to "Delete this chat after reading" and "Clear your devices" from Rahul Sen in communications (email, chat) indicate a deliberate effort to destroy forensic evidence.
*   **High Confidence:** The identified patterns are corroborated across multiple diverse data sources, including bank transactions, call detail records (CDRs), chat logs, emails, GPS data (mobile, wearable, asset, vehicle), and social media, establishing a high confidence (95-99%) in the observed suspicious activities.

**Operational Impact:**
The evidence points to a sophisticated and organized fraud or money laundering ring. The use of smurfing, mule accounts, and explicit deletion instructions demonstrates criminal intent and a concerted effort to evade detection. The swift movement of funds from multiple small transfers to a consolidated large transfer to an external "hawala" account suggests an attempt to obscure the source and ultimate beneficiary of the funds. This network represents a significant operational risk, necessitating immediate intervention.

## Key Individuals & Asset Profiling

The analysis identified four individuals and several assets/accounts as central to the suspicious activities. Their roles are inferred from their network centrality, communication patterns, financial transactions, and physical movements.

1.  **Rahul Sen (CRITICAL Risk - Score 100.0, Confidence 96%)**
    *   **Identifiers:** Rahul Sen, 9876543210, ACC1001, android_001, rahul, @rahulsen
    *   **Graph Metrics:** Highest Degree Centrality (0.5217), significant Betweenness Centrality (0.1074). This indicates Rahul Sen is the most active and central figure, with numerous direct connections and acting as a crucial bridge for information flow within the network.
    *   **Observed Role:** Primary orchestrator and initiator of the smurfing operation. He sent initial planning emails, made explicit instructions for fund transfers, and directed the clearing of communications. His frequent presence at "Chatterjee Lane, Bowbazar, Kolkata" during critical junctures further solidifies his leadership role.
    *   **Triggered Rules:** COMM_DELETION_LANGUAGE, COMM_MONEY_REQUEST, CO_CORROBORATION, FIN_SMURFING, GPS_FREQUENT_VISITS, TEMP_COLOCATION_TO_TRANSFER, TEMP_COMM_TO_TRANSFER.

2.  **Rajan Mehta (CRITICAL Risk - Score 100.0, Confidence 99%)**
    *   **Identifiers:** Rajan Mehta, 8877665544, rajan, acc9001
    *   **Graph Metrics:** High PageRank (0.0912) and Betweenness Centrality (0.1047). Rajan Mehta is a significant recipient of influence/information and acts as a critical intermediary, especially in financial flows.
    *   **Observed Role:** Primary financial mule. He received the structured incoming transfers from seven intermediary accounts (ACC2001-ACC8001) and immediately consolidated them into a single, large outbound transfer to "ACC_HAWALA". His account appears to be the central layering point for the laundered funds.
    *   **Triggered Rules:** CO_CORROBORATION, FIN_MULE_PATTERN, TEMP_COMM_TO_TRANSFER.

3.  **Vikram Khanna (CRITICAL Risk - Score 100.0, Confidence 96%)**
    *   **Identifiers:** watch_abc, vikram khanna, vikram, 9988776655, @vikramk
    *   **Graph Metrics:** High Degree Centrality (0.3043). He is an active participant, particularly in communications and physical movements.
    *   **Observed Role:** Logistical coordinator and possible cash handler. His communications mention "Cash in hand" and movements to "Howrah Station for delivery" after financial activities. He was physically co-located with Rahul Sen at "Chatterjee Lane, Bowbazar, Kolkata" during key periods.
    *   **Triggered Rules:** COMM_MONEY_REQUEST, CO_CORROBORATION, GPS_SUSPICIOUS_COLOCATION, TEMP_COLOCATION_TO_TRANSFER, TEMP_COMM_TO_TRANSFER.

4.  **Arjun (CRITICAL Risk - Score 81.5, Confidence 96%)**
    *   **Identifiers:** 9123456780, arjun, arjun ghosh, @arjung
    *   **Graph Metrics:** Moderate Degree Centrality (0.2391). An active participant in communications.
    *   **Observed Role:** Active communicator and secondary coordinator, assisting Rahul Sen. He confirmed "mule accounts are ready" and communicated with other members about coordination.
    *   **Triggered Rules:** COMM_MONEY_REQUEST, CO_CORROBORATION, GPS_SUSPICIOUS_COLOCATION.

5.  **Cab_102 (HIGH Risk - Score 59.9, Confidence 95%)**
    *   **Identifiers:** cab_102
    *   **Graph Metrics:** Low Degree Centrality (0.0652).
    *   **Observed Role:** Vehicle used for transportation and co-located with Rahul Sen at "Chatterjee Lane, Bowbazar, Kolkata" during the critical period of financial transfers. Its movement later to "Howrah Maidan, Haora" correlates with Vikram Khanna's activities.
    *   **Triggered Rules:** GPS_SUSPICIOUS_COLOCATION, TEMP_COLOCATION_TO_TRANSFER.

6.  **Tracker_001 (HIGH Risk - Score 59.9, Confidence 95%)**
    *   **Identifiers:** tracker_001
    *   **Graph Metrics:** Low Degree Centrality (0.0652).
    *   **Observed Role:** An asset tracker physically co-located with Rahul Sen at "Chatterjee Lane, Bowbazar, Kolkata" during the critical period of financial transfers. This could indicate tracking of a valuable asset or a person.
    *   **Triggered Rules:** GPS_SUSPICIOUS_COLOCATION, TEMP_COLOCATION_TO_TRANSFER.

7.  **Accounts ACC2001, ACC3001, ACC4001, ACC5001, ACC6001, ACC7001, ACC8001 (LOW Risk - Score 23.2, Confidence 99% each)**
    *   **Identifiers:** accXXXX
    *   **Graph Metrics:** Low Degree Centrality (0.0435).
    *   **Observed Role:** Intermediate "layering" accounts in the smurfing scheme. Each received a sub-threshold transfer from Rahul Sen and immediately forwarded the entire amount to Rajan Mehta, exhibiting classic mule behavior. Individually low risk, but collectively critical to the scheme.
    *   **Triggered Rules:** FIN_MULE_PATTERN.

## Suspicious Activities & Pattern Matching

The automated pipeline identified several critical patterns, confirming a highly coordinated illicit operation:

1.  **Financial Smurfing (FIN_SMURFING) - Rahul Sen (Confidence 99%)**
    *   **Pattern Breakdown:** Rahul Sen executed 7 distinct UPI transfers, each below Rs. 10,000 (ranging from Rs. 8,900 to Rs. 9,500), to seven different accounts (ACC2001 through ACC8001). The total amount smurfed was Rs. 64,400. This pattern, initiated from 2026-05-22T21:11:00, is a classic tactic to avoid triggering large transaction alerts or reporting thresholds.
    *   **Operational Risk:** This activity is a strong indicator of money laundering, designed to break down larger sums into smaller, less suspicious amounts.

2.  **Mule Account Pattern (FIN_MULE_PATTERN) - Rajan Mehta & Intermediate Accounts (Confidence 99%)**
    *   **Pattern Breakdown:** The seven accounts (ACC2001-ACC8001) received individual sub-threshold transfers from Rahul Sen. Within minutes (delays of 24-29 minutes), each account immediately transferred the full received amount to Rajan Mehta's account (ACC9001). Rajan Mehta then aggregated these funds (Rs. 64,400 total) and, also within minutes, transferred the entire sum to "ACC_HAWALA" via NEFT at 2026-05-22T22:05:00.
    *   **Operational Risk:** This 'pass-through' activity is a hallmark of a money mule operation, where accounts are used to quickly layer and move illicit funds, obscuring the original source and destination. The swift, complete forwarding of funds suggests that these accounts serve no legitimate purpose beyond facilitating the illicit transfers.

3.  **Communication Indicating Deletion (COMM_DELETION_LANGUAGE) - Rahul Sen (Confidence 95-97%)**
    *   **Pattern Breakdown:** Rahul Sen sent an email to Arjun with the subject "Tonight's Operation - Final Plan" at 2026-05-22T19:45:00, which contained forensic signals related to deletion instructions. Later, at 2026-05-22T21:25:00, he messaged the "Group_Chat": "Starting transfers now. Delete this chat after reading." Post-operation, at 2026-05-22T22:40:00, he again messaged the group: "Good work everyone. Clear your devices."
    *   **Operational Risk:** These explicit instructions to erase communications demonstrate a clear intent to destroy evidence and obstruct any potential investigation. This behavior is highly indicative of criminal activity.

4.  **Communication Requesting Money/Coordination (COMM_MONEY_REQUEST) - Rahul Sen, Arjun, Vikram Khanna (Confidence 95%)**
    *   **Pattern Breakdown:** Multiple chat messages were flagged for discussing money or transfer coordination:
        *   Arjun to "Group_Chat" (2026-05-22T20:22:00): "Rajan confirmed the mule accounts are ready. All below 10k each transfer."
        *   Rahul Sen to "Group_Chat" (2026-05-22T20:45:00): "Arjun, transfer work will happen near Park Street tonight."
        *   Arjun to "Group_Chat" (2026-05-22T20:47:00): "I am ready. Coordinate with Vikram before withdrawing."
        *   Arjun to "Group_Chat" (2026-05-22T21:10:00): "Rahul, Rajan just confirmed all 7 sub-accounts are live."
        *   Arjun to "Group_Chat" (2026-05-22T21:20:00): "ACC1001 should send the amount in small parts, below 9500 each."
        *   Vikram Khanna to "Group_Chat" (2026-05-22T21:45:00): "Cash in hand. Moving to Howrah Station now for delivery."
    *   **Operational Risk:** These messages directly outline the planning, execution, and logistical details of the illicit financial transfers, confirming a coordinated effort.

5.  **Coordinated Communication to Transfer (TEMP_COMM_TO_TRANSFER) - Rahul Sen, Rajan Mehta, Vikram Khanna (Confidence 99%)**
    *   **Pattern Breakdown:** Several instances show critical communications immediately preceding or following financial transfers:
        *   Rahul Sen called Rajan Mehta (2026-05-22T21:10:00), followed 60 seconds later by Rahul Sen's first transfer to ACC2001 (2026-05-22T21:11:00).
        *   Rajan Mehta called Rahul Sen (2026-05-22T21:15:00), precisely as Rahul Sen made a transfer to ACC6001 (2026-05-22T21:15:00).
        *   Rajan Mehta called Arjun (2026-05-22T22:00:00), followed 5 minutes later by Rajan Mehta's consolidated transfer to ACC_HAWALA (2026-05-22T22:05:00).
        *   Vikram Khanna called Rahul Sen (2026-05-22T21:05:00), preceding Rahul Sen's first transfer by 6 minutes.
    *   **Operational Risk:** The tight temporal coupling between these communications and financial transactions strongly indicates real-time coordination and instruction during the execution of the money laundering scheme.

6.  **Co-location to Transfer (TEMP_COLOCATION_TO_TRANSFER) - Rahul Sen, Vikram Khanna, Cab_102, Tracker_001 (Confidence 95%)**
    *   **Pattern Breakdown:** Rahul Sen, Vikram Khanna, Cab_102, and Tracker_001 were all detected at "Chatterjee Lane, Bowbazar, Kolkata" shortly before or during Rahul Sen's series of smurfing transfers (around 2026-05-22T20:55:00 - 21:11:00). The delays between co-location and transfer ranged from 660 to 960 seconds.
    *   **Operational Risk:** This physical rendezvous prior to the initiation of illicit financial transfers indicates in-person coordination and instruction, adding another layer of conspiratorial intent to the digital activities.

7.  **Frequent Visits (GPS_FREQUENT_VISITS) - Rahul Sen (Confidence 95%)**
    *   **Pattern Breakdown:** Rahul Sen frequently visited "Chatterjee Lane, Bowbazar, Kolkata" 5 times within a short period (2026-05-22T20:30:00 to 22:05:00).
    *   **Operational Risk:** Multiple visits to a specific location around the time of coordinated activities suggest it might be a central meeting point or operational hub for the group.

8.  **Cross-Source Corroboration (CO_CORROBORATION) (Confidence 100%)**
    *   **Pattern Breakdown:** All primary individuals (Rahul Sen, Rajan Mehta, Vikram Khanna, Arjun) and key locations (Chatterjee Lane, Howrah Station, Bow Bazar North, Howrah Maidan, Biplabi Pulin Das Street) involved show activity across 3 to 8 different data sources (bank, CDR, chat, email, GPS, social, FIR, telecom, wearable, asset, vehicle).
    *   **Operational Risk:** The consistent appearance of these entities across diverse, independent data streams significantly increases the confidence in their involvement and the overall reliability of the investigative findings.

## Timeline Narrative Reconstruction

The following narrative reconstructs the sequence of events, primarily focusing on the evening of May 22, 2026, leading up to the detection of suspicious activities on May 29, 2026:

**Evening of May 22, 2026: The Operation Unfolds**

*   **19:45 (Email Exchange - Scene_01):** The operation begins with Rahul Sen emailing Arjun under the subject "Tonight's Operation - Final Plan." The email body mentions several key individuals (Vikram Khanna, Rajan Mehta) and locations (Howrah Station), including a reference to "Hyundai." The email itself contains a forensic signal indicating a "delete instruction," setting an early tone for concealment.
*   **20:15 - 20:45 (Initial Communications & Staging - Scene_02):**
    *   Rahul Sen initiates group chat communications, stating "Arjun, tonight is the night. Park Street, 9 PM sharp," and specifying "ANDROID_001" and "9876543210" for use.
    *   Concurrently, @Rahulsen posts on Twitter about using "ANDROID_001" and "transfers split as planned across 7 accounts," mentioning @Arjung.
    *   Arjun confirms readiness in the group chat, mentioning "Vikram is also on standby near Park Street" and that "Rajan confirmed the mule accounts are ready. All below 10k each transfer."
    *   Rahul Sen places a call to Arjun and is located at "Chatterjee Lane, Bowbazar, Kolkata." Vikram Khanna messages the group chat, confirming his proximity to Park Street.
*   **20:45 - 21:15 (Critical Rendezvous & Smurfing Initiation - Scene_03):**
    *   Communications intensify. Arjun calls Rahul Sen. Rahul Sen is seen moving near "Chatterjee Lane," while Arjun is at "Surya Sen Street, Baithakkhana, Kolkata."
    *   Rahul Sen messages the group chat about "transfer work" near Park Street.
    *   A critical physical rendezvous occurs at "Chatterjee Lane, Bowbazar, Kolkata": Rahul Sen calls Vikram Khanna while they are physically co-located, along with "Tracker_001" and "Cab_102." This co-location is corroborated by mobile GPS, wearable device, asset tracker, and vehicle tracker data.
    *   @Vikramk posts on Facebook confirming his position near Park Street, "waiting for signal from Rahul." @Arjung posts on Instagram, mentioning Rahul and Vikram coordinating near Park Street.
    *   Rahul Sen calls Rajan Mehta. Immediately following this call, between 21:11:00 and 21:17:00, Rahul Sen initiates a series of 7 UPI transfers, each below Rs. 10,000, to various intermediary accounts (ACC2001-ACC8001), successfully executing the smurfing operation.
*   **21:15 - 21:45 (Mule Account Aggregation - Scene_04):**
    *   Rajan Mehta calls Rahul Sen. Rajan Mehta is connected to "Cell Tower (Twr_Kol_315)."
    *   From 21:35:00 to 21:41:00, the intermediary accounts (ACC2001-ACC8001) swiftly transfer all the received smurfed funds to Rajan Mehta's account via IMPS.
    *   Rahul Sen continues communications, making a call to Arjun. Arjun is at "Bow Bazar North, Kolkata."
    *   Vikram Khanna is observed moving from "Sri Gopal Mullick Ln" to "Bow Bazar North, Kolkata" via wearable device.
*   **21:45 - 22:15 (Delivery & Final Outbound Transfer - Scene_05):**
    *   Vikram Khanna calls Rajan Mehta. He then messages the group chat, "Cash in hand. Moving to Howrah Station now for delivery."
    *   Rajan Mehta calls Arjun.
    *   Rahul Sen calls Vikram Khanna.
    *   At 22:05:00, Rajan Mehta executes a large NEFT transfer of the consolidated Rs. 64,400 to "ACC_HAWALA." This is the critical mule outbound transfer.
    *   @Vikramk posts on Facebook, "Reached Howrah Station after the withdrawal. Device WATCH_ABC is still on. Job done."
    *   "Cab_102" is observed moving towards "Howrah Maidan, Haora."
*   **22:15 - 22:45 (Post-Operation Confirmation & Concealment - Scene_06):**
    *   Vikram Khanna calls Arjun.
    *   Rajan Mehta calls Rahul Sen.
    *   Vikram Khanna, now at "Howrah Maidan, Haora," messages the group: "Reached Howrah Station. Package handed over successfully."
    *   Critically, Rahul Sen messages the group chat: "Good work everyone. Clear your devices," reinforcing the intent to destroy evidence.
*   **22:45 - 23:15 (Final Communications - Scene_07):**
    *   @Arjung posts on Instagram, "All clear. @VikramK handled the delivery perfectly. Rajan confirmed receipt at Howrah."
    *   Rahul Sen and Arjun place calls to Rajan Mehta, likely confirming the successful completion of the operation and adherence to concealment protocols.
*   **May 29, 2026 (Later Activity - Scene_339 & Scene_344):**
    *   A "TRANSFERRED_MONEY" relation between Rahul Sen and Arjun is recorded in an FIR document, dated May 29, 2026, 21:00:00, suggesting this financial link was later identified by investigators.
    *   CCTV camera detections of unspecified vehicles at a traffic signal occur late on May 29, 2026, 23:30:51, possibly part of broader surveillance or subsequent investigative leads.

## Investigation Recommendations & Next Steps

Based on the synthesis of intelligence, the following prioritized recommendations are provided:

1.  **Immediate Financial Action:**
    *   **Freeze Funds:** Initiate urgent contact with relevant financial institutions to freeze funds in "ACC_HAWALA." Request full beneficiary details and transaction history for this account.
    *   **Account Audit:** Request comprehensive KYC and complete transaction histories for Rahul Sen's account (ACC1001), Rajan Mehta's account (ACC9001), and all intermediary accounts (ACC2001-ACC8001). Investigate the origins of the funds in ACC1001 and the ultimate destination of funds from ACC_HAWALA.
    *   **Law Enforcement Liaison:** Share all financial transaction details, especially concerning ACC_HAWALA, with relevant financial intelligence units (FIUs) and law enforcement agencies for tracing and asset recovery.

2.  **Digital Forensics & Evidence Seizure:**
    *   **Device Seizure:** Obtain judicial authorization to seize all digital devices (phones, computers, wearable devices, asset trackers) belonging to Rahul Sen, Rajan Mehta, Vikram Khanna, and Arjun (based on their critical risk profiles).
    *   **Data Extraction:** Conduct full forensic imaging and analysis of seized devices, prioritizing chat logs, call histories, email data, and social media activity. Pay particular attention to deleted content, given the explicit "delete instruction" signals.
    *   **Cloud Data:** Investigate linked cloud accounts (email, social media, messaging apps) for additional evidence or backups.

3.  **Geolocation & Physical Surveillance:**
    *   **CCTV Review:** Obtain and review CCTV footage from 2026-05-22, specifically between 20:30:00 and 21:15:00, for "Chatterjee Lane, Bowbazar, Kolkata," focusing on identifying individuals (Rahul Sen, Vikram Khanna), vehicles (Cab_102, any associated with Tracker_001), and confirming physical interactions.
    *   **Additional CCTV:** Extend CCTV review to "Park Street area," "Howrah Station," and "Howrah Maidan, Haora" for coordinating movements, especially between 21:45:00 and 22:45:00.
    *   **Vehicle Identification:** Utilize the reported vehicle "white Hyundai TN09BY9726" mentioned by @Vikramk on Facebook for further investigation and tracking.

4.  **Interviews & Interrogations:**
    *   **Prioritized Interviews:** Conduct formal interviews with Rahul Sen, Rajan Mehta, Vikram Khanna, and Arjun, prioritizing them based on their centrality and identified roles. Present the corroborated evidence to illicit confessions or further details.
    *   **Network Expansion:** Use information from interviews to identify any additional individuals or entities involved in the broader criminal network.

5.  **Further Analytical Review:**
    *   **Reverse Engineering:** Attempt to reverse engineer the source of the funds initially transferred by Rahul Sen, if not already apparent from bank records.
    *   **Pattern Analysis:** Continuously monitor for similar smurfing or mule account patterns involving these individuals or associated entities across broader datasets.
    *   **Social Media Analysis:** Conduct deeper analysis of social media activity for all identified individuals, looking for connections to other suspicious networks or individuals.

This report provides a solid foundation for operational action. The high confidence in the findings necessitates swift and decisive investigative steps.