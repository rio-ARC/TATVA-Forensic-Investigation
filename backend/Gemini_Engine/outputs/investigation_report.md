# FORENSIC INVESTIGATION REPORT

## Executive Summary

This report details a coordinated financial fraud and potential money laundering operation active between May 22, 2026, and May 29, 2026. Analysis of graph topology, rule-based flags, and chronological event reconstruction reveals a sophisticated network involving at least four key individuals: Rahul Sen, Rajan Mehta, Vikram Khanna, and Arjun. The operation is characterized by a "smurfing" scheme, where a significant sum (Rs. 64,400) was broken into multiple sub-threshold transactions to evade detection, followed by aggregation and onward transfer.

Key operational findings include:
*   **Centralized Orchestration:** Rahul Sen, identified as the most connected and influential actor, initiated the illicit financial transfers and issued critical instructions, including orders to delete communications.
*   **Coordinated Movements:** Multiple physical rendezvous points were observed at Chatterjee Lane and Bow Bazar North, Kolkata, indicating in-person coordination among key operatives during the active phase of the scheme.
*   **Covert Communication:** The use of encrypted group chats with explicit instructions for sub-threshold transfers and urgencies around "cash in hand" and "delivery" points to a deliberate attempt at concealment and rapid execution.
*   **Mule Account Utilization:** A network of seven intermediate accounts was used to receive fragmented funds from Rahul Sen before consolidating them to Rajan Mehta, who subsequently transferred the aggregated amount to a suspicious 'ACC_HAWALA'.

The coordinated interactions across telecom, location, and banking channels strongly suggest a pre-meditated and systematically executed financial crime. The operational impact is significant, demonstrating a clear attempt to bypass anti-money laundering controls through structured transactions and encrypted communications.

## Key Individuals & Asset Profiling

The investigation identified four primary human actors and several critical infrastructure/asset entities within the suspicious network, profiled by their connectivity and influence:

1.  **Rahul Sen (MASTER_b41353c7) - Primary Orchestrator & Fund Initiator:**
    *   **Master Type:** PERSON
    *   **Centrality Scores:**
        *   **Degree Centrality (0.5217):** Highest in the network, indicating a large number of direct connections. Rahul is extensively connected to other individuals, places, accounts, and infrastructure.
        *   **Betweenness Centrality (0.1074):** High, suggesting he acts as a crucial bridge or intermediary for information and transaction flow between other parts of the network.
        *   **PageRank (0.034):** Reflects moderate influence within the overall network structure.
    *   **Observed Role:** Rahul Sen is the central figure, initiating the smurfing transactions from "ACC1001" (resolved from his profile) and his device "android_001." He sends critical "delete instruction" emails and urgent chat messages, and is physically present at key rendezvous points. His activity spans 8 diverse data sources (bank, CDR, chat, email, FIR, mobile GPS, social, telecom), underscoring his pervasive involvement.

2.  **Rajan Mehta (MASTER_ee1fa35b) - Financial Aggregator & Mule Coordinator:**
    *   **Master Type:** PERSON
    *   **Centrality Scores:**
        *   **Degree Centrality (0.3261):** High, indicating numerous direct connections, particularly financial ones.
        *   **Betweenness Centrality (0.1047):** Significantly high, suggesting he is critical for connecting disparate parts of the financial network, specifically as the recipient of the smurfed funds and the onward transferor.
        *   **PageRank (0.0912):** Highest in the network, indicating significant influence and importance, likely due to his role in handling the bulk of the funds.
    *   **Observed Role:** Rajan Mehta (associated with "acc9001") is the primary beneficiary of the smurfed funds, receiving Rs. 64,400 in 7 separate IMPS transfers from the mule accounts. He subsequently transferred this entire sum to "ACC_HAWALA" using NEFT. Chat logs confirm he "confirmed the mule accounts are ready," positioning him as the coordinator for the recipient accounts. He appears across 4 data sources.

3.  **Vikram Khanna (MASTER_f24caf16) - Logistical Coordinator & Cash Handler:**
    *   **Master Type:** PERSON
    *   **Centrality Scores:**
        *   **Degree Centrality (0.3043):** High, indicating active engagement within the communication and physical movement network.
        *   **Betweenness Centrality (0.0379):** Moderate, suggesting some bridging role but less critical than Rahul or Rajan for overall network flow.
        *   **PageRank (0.0185):** Lower influence compared to Rahul or Rajan.
    *   **Observed Role:** Vikram Khanna (associated with "watch_abc" and phone "9988776655") is involved in physical coordination and likely cash handling. He is mentioned in chats regarding coordination and confirms "Cash in hand. Moving to Howrah Station now for delivery." He participated in a key rendezvous at Chatterjee Lane. His activity is corroborated across 6 data sources.

4.  **Arjun (MASTER_6137f90b) - Operational Assistant & Key Communicator:**
    *   **Master Type:** PERSON
    *   **Centrality Scores:**
        *   **Degree Centrality (0.2391):** Solid, indicating an active role in communications.
        *   **Betweenness Centrality (0.027):** Moderate, highlighting his involvement in coordinating information flow, especially within the group chat.
        *   **PageRank (0.0294):** Moderate influence, supporting his role as an active participant.
    *   **Observed Role:** Arjun (associated with phone "9123456780") receives the initial "delete instruction" email from Rahul Sen. He actively communicates in the "Group_Chat," confirming mule account readiness and coordinating with Vikram. He also participated in the rendezvous at Bow Bazar North. He appears across 5 data sources.

5.  **Group_Chat (MASTER_cc9e76cc) - Primary Communication Hub:**
    *   **Master Type:** INFRASTRUCTURE
    *   **Centrality Scores:** High in-degree centrality (0.0652) due to messages from multiple actors, but zero betweenness and out-degree, as it is a recipient of communications.
    *   **Observed Role:** This group chat served as the central point for real-time coordination and instruction dissemination among Rahul, Arjun, and Vikram regarding the smurfing operation and physical movements.

6.  **Chatterjee Lane, Bowbazar, Kolkata (MASTER_ad6e0d66) - Initial Rendezvous Point:**
    *   **Master Type:** PLACE
    *   **Centrality Scores:** High degree centrality (0.2174) and moderate betweenness (0.0263), indicating it was a significant meeting point for multiple entities.
    *   **Observed Role:** A critical physical location where Rahul Sen, Vikram Khanna, and associated assets (Tracker_001, Cab_102) co-located, likely for initial coordination or transfer of physical assets/instructions. It appears across 7 data sources.

7.  **ACC_HAWALA (MASTER_d551104f) - Suspicious Final Destination Account:**
    *   **Master Type:** ENTITY (Account)
    *   **Centrality Scores:** Only in-degree (0.0217), indicating it solely received funds.
    *   **Observed Role:** This account received the aggregated sum of Rs. 64,400 from Rajan Mehta, making it a critical endpoint for the laundered funds.

## Suspicious Activities & Pattern Matching

The automated rule validation pipeline identified 22 suspicious flags, including 1 CRITICAL, 9 HIGH, and 12 MEDIUM severity alerts, detailing a coordinated effort to move illicit funds and cover tracks.

### 1. Financial Smurfing (CRITICAL)

*   **Rule Triggered:** `SMURFING_DETECTED`
*   **Description:** Rahul Sen (MASTER_b41353c7) executed 7 rapid transfers, each under Rs. 10,000, totaling Rs. 64,400, within a 6-minute window (21:11 - 21:17) on 2026-05-22. These funds were directed to various 'mule' accounts (ACC2001, ACC3001, ACC4001, ACC5001, ACC6001, ACC7001, ACC8001).
*   **Mechanics:** The transfers were initiated via UPI from Rahul Sen's account. Immediately following, from 21:35 to 21:41 on the same date, these 7 mule accounts transferred the exact amounts received to Rajan Mehta's account (ACC9001) via IMPS. This classic smurfing pattern aims to circumvent reporting thresholds for large transactions, fragmented and then aggregated. This highly structured and rapid sequence confirms deliberate evasion of financial controls.
*   **Operational Risk:** High risk of money laundering, utilizing multiple intermediary accounts to obscure the origin and destination of funds.

### 2. Forensic Hit Signals (HIGH/MEDIUM)

Numerous communication intercepts revealed explicit coordination and intent:
*   **Delete Instruction (HIGH):** An email from Rahul Sen to Arjun on 2026-05-22 at 19:45:00, with the subject "Tonight's Operation - Final Plan," contained a "delete_instruction" flag. This indicates a clear intent to erase evidence and conceal the operation.
*   **Money Reference & Coordination in Chat (MEDIUM):**
    *   Arjun to Group_Chat (2026-05-22, 20:22:00): "Rajan confirmed the mule accounts are ready. All below 10k each transfer." (Flags: `has_money_ref`, `has_coordination`). This message explicitly outlines the smurfing strategy and confirms Rajan's role.
    *   Rahul Sen to Group_Chat (2026-05-22, 20:45:00): "Arjun, transfer work will happen near Park Street tonight." (Flag: `has_money_ref`). This links the financial operation to a physical location.
    *   Arjun to Group_Chat (2026-05-22, 20:47:00): "I am ready. Coordinate with Vikram before withdrawing." (Flag: `has_coordination`). This highlights Vikram's role in the withdrawal phase.
    *   Arjun to Group_Chat (2026-05-22, 21:20:00): "ACC1001 should send the amount in small parts, below 9500 each." (Flag: `has_money_ref`). Further explicit instruction on smurfing from Rahul's account.
*   **Urgency & Deletion Instructions in Chat (HIGH):**
    *   Rahul Sen to Group_Chat (2026-05-22, 21:25:00): "Starting transfers now. Delete this chat after reading." (Flag: `has_urgency`). Direct order to delete, coupled with the commencement of transfers, reinforces intent to conceal.
    *   Vikram Khanna to Group_Chat (2026-05-22, 21:45:00): "Cash in hand. Moving to Howrah Station now for delivery." (Flag: `has_urgency`). Confirms the successful withdrawal of funds and onward movement for delivery, with a sense of urgency.
*   **Operational Risk:** These signals provide strong evidence of criminal intent, pre-planning, and active concealment, directly corroborating the financial smurfing.

### 3. Communication Bursts (MEDIUM)

*   **Rule Triggered:** `COMMUNICATION_BURST`
*   **Description:** Rahul Sen and the Group_Chat engaged in 5 interactions within a 35-minute window (20:15 - 20:50) on 2026-05-22.
*   **Mechanics:** This burst of communication occurred during the initial planning and setup phase of the operation, as messages were exchanged regarding logistics, mule accounts, and transfer instructions.
*   **Operational Risk:** Intense communication bursts among key actors during critical operational windows are indicative of high-stakes coordination and potentially illicit activities.

### 4. Co-locations / Rendezvous (HIGH)

Two critical physical co-locations were detected, indicating in-person coordination:
*   **Rendezvous 1 (Chatterjee Lane):** Rahul Sen, Tracker_001, Vikram Khanna, and Cab_102 were co-located at Chatterjee Lane, Bowbazar, Kolkata, between 20:45 and 21:00 on 2026-05-22.
*   **Rendezvous 2 (Bow Bazar North):** Arjun, Rahul Sen, and Vikram Khanna were co-located at Bow Bazar North, Kolkata, between 21:20 and 21:30 on 2026-05-22.
*   **Mechanics:** These rendezvous points occur precisely before and during the smurfing transactions and cash withdrawal/delivery phases. The presence of a vehicle (Cab_102) and an asset tracker (Tracker_001) suggests logistical support for movements of individuals or assets.
*   **Operational Risk:** Co-location of multiple key individuals during critical operational windows provides strong evidence of direct, in-person coordination for illicit activities.

### 5. Cross-Source Corroboration (HIGH/MEDIUM)

Key entities consistently appear across multiple independent data sources, reinforcing their importance and the robustness of the intelligence:
*   **Rahul Sen:** Appears across 8 data sources (bank_transaction, cdr_record, chat, emails, fir_document, mobile_gps, social, telecom_tower). (HIGH)
*   **Chatterjee Lane, Bowbazar, Kolkata:** Appears across 7 data sources (asset_tracker, gps_analysis, investigator_annotation, mobile_gps, telecom_tower, vehicle_tracker, wearable_device). (HIGH)
*   **Vikram Khanna:** Appears across 6 data sources (cdr_record, chat, emails, social, telecom_tower, wearable_device). (HIGH)
*   **Arjun:** Appears across 5 data sources (cdr_record, chat, emails, fir_document, telecom_tower). (HIGH)
*   **Rajan Mehta:** Appears across 4 data sources (bank_transaction, cdr_record, chat, emails). (MEDIUM)
*   **Bow Bazar North, Kolkata:** Appears across 4 data sources (gps_analysis, mobile_gps, telecom_tower, wearable_device). (MEDIUM)
*   **Howrah Maidan, Haora:** Appears across 4 data sources (gps_analysis, telecom_tower, vehicle_tracker, wearable_device). (MEDIUM)
*   **Operational Risk:** High cross-source corroboration validates the existence and active involvement of these entities in the reported activities, increasing the confidence in the intelligence.

## Timeline Narrative Reconstruction

The following reconstructs the sequence of events over a critical 5-hour period on May 22, 2026, leading to the completion of the smurfing operation:

### Scene 1: Initial Planning & Instructions (19:45 - 20:15)
*   **19:45:** Rahul Sen emails Arjun with the subject "Tonight's Operation - Final Plan," explicitly instructing Arjun to delete the email after reading. The email also mentions Vikram Khanna, Howrah Station, Hyundai, and Rajan Mehta, outlining the key players and a critical location.

### Scene 2: Pre-Operation Coordination (20:15 - 20:45)
*   **20:15:** Rahul Sen messages the "Group_Chat," confirming "Park Street, 9 PM sharp" and posts on Twitter about using "ANDROID_001" for split transfers. He tags @ArjunG.
*   **20:17:** Arjun replies in Group_Chat, confirming readiness and Vikram's standby near Park Street.
*   **20:20:** Rahul Sen confirms he will use "ANDROID_001" and keep "9876543210" active.
*   **20:22:** Arjun informs the Group_Chat that "Rajan confirmed the mule accounts are ready. All below 10k each transfer," clearly stating the smurfing strategy.
*   **20:25:** Rahul Sen instructs the Group_Chat that "ACC1001 will initiate. Split into at least 7 tranches."
*   **20:30:** Rahul Sen calls Arjun (185s, outgoing) while located at Chatterjee Lane, Bowbazar, Kolkata, connecting to Cell Tower (Twr_Kol_102). Vikram Khanna messages the Group_Chat that his "WATCH_ABC shows I am 500 meters from Park Street."
*   **20:40:** Rahul Sen again posts on Twitter, mentioning "Park Street" and @ArjunG, indicating final readiness.

### Scene 3: Coordinated Setup & Initial Transfers (20:45 - 21:15) - Peak Activity
*   **20:45:** Arjun calls Rahul Sen (60s, incoming). Rahul Sen is moving at Chatterjee Lane, Bowbazar, Kolkata, while Arjun is moving at Surya Sen Street, Baithakkhana, Kolkata. Rahul Sen messages Group_Chat about "transfer work" near Park Street.
*   **20:47:** Arjun messages Group_Chat, "I am ready. Coordinate with Vikram before withdrawing."
*   **20:50:** Rahul Sen messages Group_Chat, reiterating device and number usage.
*   **20:55:** Rahul Sen calls Vikram Khanna (240s, outgoing). Tracker_001 is stationary at Chatterjee Lane, Bowbazar, Kolkata.
*   **20:58:** Vikram Khanna is moving at Chatterjee Lane, Bowbazar, Kolkata (via wearable device).
*   **21:00:** Rahul Sen is stationary at Chatterjee Lane, Bowbazar, Kolkata. Cab_102 is also stationary there. Vikram posts on Facebook about being "Parked the white Hyundai...near Park Street. Waiting for signal from Rahul."
*   **21:05:** Vikram Khanna calls Rahul Sen (90s, incoming) and messages Group_Chat, confirming his position near Park Street.
*   **21:10:** Rahul Sen calls Rajan Mehta (310s, outgoing). Arjun messages Group_Chat that "Rajan just confirmed all 7 sub-accounts are live." Arjun posts on Instagram, mentioning Rahul and Vikram, about waiting near Park Street.
*   **21:11 - 21:14:** Rahul Sen initiates the first four smurfing transfers via UPI from his account to ACC2001 (Rs. 9,400), ACC3001 (Rs. 9,200), ACC4001 (Rs. 9,500), and ACC5001 (Rs. 8,900).

### Scene 4: Financial Transfers & Movement (21:15 - 21:45)
*   **21:15:** Rajan Mehta calls Rahul Sen (45s, incoming). Vikram Khanna is stationary at Sri Gopal Mullick Ln, Bowbazar, Kolkata. Movement is recorded from Chatterjee Lane to Sri Gopal Mullick Ln. Rahul Sen transfers to ACC6001 (Rs. 9,300).
*   **21:16 - 21:17:** Rahul Sen completes the smurfing with transfers to ACC7001 (Rs. 9,100) and ACC8001 (Rs. 9,000).
*   **21:20:** Arjun calls Vikram Khanna (200s, outgoing) while Arjun is stationary at Bow Bazar North, Kolkata. Movement from Surya Sen Street to Bow Bazar North is detected. Arjun messages Group_Chat, reminding that "ACC1001 should send the amount in small parts, below 9500 each" (despite transfers being complete).
*   **21:25:** Rahul Sen messages Group_Chat, "Starting transfers now. Delete this chat after reading." (This message appears delayed after the actual transfers started, possibly a final instruction or confirmation).
*   **21:30:** Rahul Sen is moving at Bow Bazar North, Kolkata. Cab_102 is moving to Biplabi Pulin Das Street, City College, Kolkata. Vikram Khanna is moving at Bow Bazar North, Kolkata. Movement detected from Chatterjee Lane to Bow Bazar North (Rahul/Vikram) and to Biplabi Pulin Das Street (Cab_102).
*   **21:35:** Rahul Sen calls Arjun (320s, outgoing) while located at Chatterjee Lane.
*   **21:35 - 21:41:** The 7 mule accounts (ACC2001-ACC8001) rapidly transfer their received funds via IMPS to Rajan Mehta (ACC9001).

### Scene 5: Consolidation & Delivery (21:45 - 22:15)
*   **21:45:** Vikram Khanna calls Rajan Mehta (180s, outgoing). Tracker_001 is moving to Maniktala, Kolkata. Vikram messages Group_Chat: "Cash in hand. Moving to Howrah Station now for delivery."
*   **22:00:** Rajan Mehta calls Arjun (75s, incoming).
*   **22:05:** Rahul Sen calls Vikram Khanna (240s, outgoing) while stationary at Chatterjee Lane. Arjun messages Group_Chat to "Confirm when Vikram reaches Howrah. I will alert Rajan." Vikram posts on Facebook: "Reached Howrah Station after the withdrawal... Job done." Critically, Rajan Mehta transfers the aggregated Rs. 64,400 to ACC_HAWALA via NEFT.
*   **22:10:** Cab_102 is moving to Howrah Maidan, Haora.

### Scene 6: Post-Operation Movement & Confirmation (22:15 - 22:45)
*   **22:20:** Vikram Khanna calls Arjun (130s, outgoing). Rahul Sen is moving at Bow Bazar North, Kolkata.
*   **22:35:** Rajan Mehta calls Rahul Sen (45s, incoming). Rahul Sen is moving at Biplabi Pulin Das Street, City College, Kolkata.
*   **22:38:** Vikram Khanna is stationary at Howrah Maidan, Haora, and messages Group_Chat, "Reached Howrah Station. Package handed over successfully."
*   **22:40:** Tracker_001 is moving to Bidhannagar. Rahul Sen sends a final message to Group_Chat, "Good work everyone. Clear your devices."

### Scene 7: Final Communications (22:45 - 23:15)
*   **22:45:** Arjun posts on Instagram, "All clear. @VikramK handled the delivery perfectly. Rajan confirmed receipt at Howrah."
*   **22:50:** Rahul Sen calls Rajan Mehta (165s, outgoing).
*   **23:00:** Arjun calls Rajan Mehta (95s, outgoing).

### Later Events (May 29, 2026)
*   **21:00:** An FIR document references Rahul Sen transferring money to Arjun.
*   **23:30:** CCTV camera at a traffic signal detects various vehicles, possibly unrelated or part of further illicit activity.

## Investigation Recommendations & Next Steps

Based on the synthesis of graph topology, rule validation flags, and chronological event reconstruction, the following actionable recommendations are prioritized for further investigation:

1.  **Financial Account Freezing & KYC Audit:**
    *   **Immediately freeze ACC_HAWALA (MASTER_d551104f):** This account is the ultimate recipient of the laundered funds. Urgent action is required to prevent further dissipation of illicit gains.
    *   **Request comprehensive KYC records:** Obtain full Know Your Customer documentation for all involved accounts, particularly ACC1001 (Rahul Sen's account) and the 7 mule accounts (ACC2001-ACC8001), from their respective financial institutions. Identify the beneficial owners and any associated entities.
    *   **Trace funds from ACC_HAWALA:** Initiate requests to trace subsequent transfers from ACC_HAWALA to identify the final beneficiaries and any layering activities.

2.  **Physical Surveillance & CCTV Review:**
    *   **CCTV Review - Chatterjee Lane (MASTER_ad6e0d66):** Obtain and review CCTV footage from Chatterjee Lane, Bowbazar, Kolkata, for the window of 2026-05-22, 20:40 - 21:05. Focus on identifying Rahul Sen, Vikram Khanna, and Cab_102 (MASTER_472a3eae) to corroborate their physical rendezvous and potential asset transfers.
    *   **CCTV Review - Bow Bazar North (MASTER_59760bb7):** Obtain and review CCTV footage from Bow Bazar North, Kolkata, for 2026-05-22, 21:15 - 21:35. Focus on identifying Arjun, Rahul Sen, and Vikram Khanna during their co-location.
    *   **CCTV Review - Howrah Station (MASTER_e32ebe48):** Obtain and review CCTV footage around Howrah Station for 2026-05-22, 21:40 - 22:10, to confirm Vikram Khanna's presence and any "delivery" activity mentioned in chats.
    *   **Vehicle Identification:** Prioritize identification and tracking of Cab_102 and the white Hyundai TN09BY9726 mentioned by @Vikramk (if not already done).

3.  **Digital Forensics & Data Acquisition:**
    *   **Secure "Group_Chat" Data:** Issue legal requests to the relevant platform provider (e.g., WhatsApp/Telegram) to secure full chat logs for "Group_Chat" (MASTER_cc9e76cc), specifically for the period of 2026-05-22.
    *   **Device Log Audit:** Acquire and audit device logs for "ANDROID_001" (Rahul Sen) and "WATCH_ABC" (Vikram Khanna) for evidence of data deletion, communication patterns, and GPS history.
    *   **Social Media Account Audit:** Request data from Twitter and Instagram for @Rahulsen (MASTER_656f09cf), @Arjung (MASTER_425adff9), and @Vikramk (MASTER_4f3dc74c) for 2026-05-22, to retrieve any deleted or relevant posts.

4.  **Prioritized Interviews:**
    *   **Rahul Sen (MASTER_b41353c7):** High priority, due to his central role in orchestration, initiation of smurfing, and explicit deletion instructions.
    *   **Rajan Mehta (MASTER_ee1fa35b):** High priority, as the aggregator of smurfed funds and the initiator of the suspicious transfer to ACC_HAWALA.
    *   **Vikram Khanna (MASTER_f24caf16):** Medium priority, for his involvement in physical coordination and alleged cash handling.
    *   **Arjun (MASTER_6137f90b):** Medium priority, as a key communicator and recipient of direct instructions.

5.  **Expand Network Investigation:**
    *   **Unidentified Entities:** Investigate the nature and identity of 'MASTER_e6f4f60a', 'Email_Address_Cc44D0C6', and 'Email_Address_5029504C' mentioned in Rahul Sen's initial email to determine if they are additional conspirators or proxies.
    *   **Source of FIR Document:** Ascertain the origin and details of the FIR document referencing Rahul Sen and Arjun's money transfer to understand the broader context or any prior investigations.

These steps are designed to swiftly collect further evidence, identify additional actors, and disrupt the ongoing financial fraud network.