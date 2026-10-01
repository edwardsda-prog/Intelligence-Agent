# Lab 1: Data Foundations & Multi-Domain Intelligence

**Target Persona:** UK Ministry of Defence (MOD) Joint Command Staff & Multi-Domain Analysts  
**Operational Context:** Multi-Domain Command and Control (MDC2 / JADC2) Data Foundations  
**Architecture Reference:** [architecture.md §3.1](../lab0/architecture.md) & [Spec.md §2.1, §3.1](../Spec.md)  
**Security Classification:** Demonstrator  

---

## 📋 Prerequisites & Prior Lab Dependencies

> [!NOTE]
> **Lab 1 is the foundational entry point** for the entire workshop. It establishes the persistent BigQuery tables and Cloud Storage assets required by subsequent labs.

| Prerequisite Dimension | Specification / Requirement |
| :--- | :--- |
| **Required Prior Labs** | **None** (Foundational Starting Point) |
| **Local Environment** | Python 3.11+ with Google Cloud SDK (`gcloud`, `bq`) |
| **GCP Infrastructure** | Active Google Cloud Project with Cloud Shell or `gcloud` CLI authenticated |
| **APIs Required** | BigQuery API (`bigquery.googleapis.com`), Cloud Storage API (`storage.googleapis.com`) |
| **Produced Artifacts** | BigQuery dataset `learning_labs_mission_data`, GCS bucket `gs://${PROJECT_ID}-learning-labs-humint-docs/` containing 10 tactical HUMINT PDFs |
| **Fast-Forward Command** | `./lab1/code/setup_lab1.sh` (executes schema creation, sample record population, and PDF generation) |

---

## Objective & Architectural Rationale
Establish the secure foundational data tier for multi-domain operations (MDO / JADC2). Modern joint command decisions cannot rely on stovepiped sensor silos. In accordance with the **Google Cloud Well-Architected Framework (WAF)** and the **Learning Lab Mission Intelligence Specification (`Spec.md §2.1`)**, you will establish an integrated Common Operational Picture (COP) in BigQuery (`learning_labs_mission_data`).

This structured data layer unifies six mission intelligence domains:
1. **Radar Telemetry (`radar_telemetry`)**: Kinematic track vectors, platform types, velocities, and tactical signatures.
2. **Electronic Warfare (`ew_intercepts`)**: Electronic Support Measures (ESM) emitter intercepts, frequencies (GHz), and PRFs.
3. **Satellite Reconnaissance (`satellite_recon`)**: Synthetic Aperture Radar (SAR), optical, and infrared detections with confidence metrics.
4. **Cyber Threat Intelligence (`cyber_threat_intel`)**: Threat actors (e.g., `APT-BEAR`), compromised tactical frequencies, and indicators of compromise.
5. **Human Intelligence (`humint_reports`)**: Field observations and observer reliability ratings.
6. **Friendly Blue Force Assets (`friendly_assets`)**: Allied naval/air defense perimeters, callsigns, and readiness postures.

Furthermore, you will verify the pre-joined analytical view `v_multi_domain_intelligence`, which downstream autonomous AI agents (powered by ADK 2.0 and MCP in Labs 2–5) will query dynamically.

---

## 🏛️ Enterprise Architectural Invariants
* **Enterprise Portability:** All dataset definitions, schemas, and queries are designed for standard Google Cloud regions and translate directly to isolated enterprise cloud environments.
* **Decoupled Tool Consumption:** This database will not embed agent logic; instead, in Lab 3 it will be exposed as a sandboxed tool via the **Model Context Protocol (MCP)** on Cloud Run.

---

## 🏛️ Google Best Practice: Enterprise Data Foundations for Agentic AI

When architecting production multi-domain platforms to feed autonomous AI agents, Google Recommended Best Practices define four foundational data design principles:

### 1. Hybrid Data Tiering (Structured vs. Unstructured)
* **The Problem**: Attempting to force unstructured field reports (PDFs, imagery) into relational databases, or trying to perform deterministic numerical aggregations (like calculating average radar velocities) using vector databases, leads to brittle and expensive architectures.
* **Google Best Practice Solution**: Decouple the intelligence data tiers. In this workshop, high-velocity structured telemetry (Radar, EW, Cyber) is centralized in **BigQuery** for deterministic SQL analytics. Unstructured multimodal assets (HUMINT PDFs) are staged in **Google Cloud Storage (GCS)**, which will later be ingested into **Vertex AI Search** (Lab 5) for semantic retrieval.
* **📚 Further Reading:** [Google Cloud Architecture Center: Data lifecycle and hybrid data tiering](https://cloud.google.com/architecture/data-lifecycle-cloud-platform)

### 2. Analytical Views for Agent Prompt Simplicity
* **Defending Against LLM Schema Hallucinations**: Asking an LLM to navigate complex 6-way SQL joins on the fly across normalized mission tables often results in hallucinated syntax or dropped context.
* **Google Best Practice Solution**: Pre-join the data in the warehouse. In this lab, we create the `v_multi_domain_intelligence` analytical view, which cross-references Radar, EW, Satellite, Cyber, and Blue Force assets. The AI agent only needs to query this single wide view, dramatically improving reliability and reducing token costs.
* **📚 Further Reading:** [BigQuery Documentation: Introduction to logical views](https://cloud.google.com/bigquery/docs/views-intro)

### 3. Right-Sizing Intelligence (WAF AI/ML Operational Excellence)
* **Rule**: *"If a deterministic SQL join solves it, do not use an LLM."*
* Google Best Practice mandates a tiered approach to intelligence:
  - **Relational Aggregation & Spatial Joins**: Handle natively in BigQuery (`v_multi_domain_intelligence`).
  - **Predictive Kinematics & Anomaly Detection**: BigQuery ML / TimesFM foundation models.
  - **Unstructured Multi-Modal Reasoning**: Reserve Gemini Foundation Models (via ADK 2.0 in Labs 2–5) strictly for ambiguous synthesis, cross-sensor reasoning, and intent translation.
* **📚 Further Reading:** [BigQuery ML Documentation: Introduction to BQML](https://cloud.google.com/bigquery/docs/bqml-introduction)

---

## 📖 Beginner's Guide: Getting Started with BigQuery Studio

If you have never used Google Cloud BigQuery before, follow this quick 3-step walkthrough to get familiar with the interface:

### Step 1: Open BigQuery Studio
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. In the top search bar, type **BigQuery** and select **BigQuery Studio** (or open the left navigation menu **☰ ➔ BigQuery ➔ Studio**).
3. Look at the **Explorer** panel on the left side of your screen:
   - You will see your **Project ID**.
   - Expand your Project ID to find the dataset: `learning_labs_mission_data`.
   - Expand `learning_labs_mission_data` to see the tables (`radar_telemetry`, `ew_intercepts`, `satellite_recon`, `cyber_threat_intel`, `humint_reports`, `friendly_assets`) and the view (`v_multi_domain_intelligence`).

### Step 2: Open a SQL Query Tab
1. Click the **`+` (Compose new query)** button in the top workspace tab bar.
2. An empty SQL editor tab will open.

### Step 3: Run a SQL Query
1. Paste your SQL script into the editor area.
2. Click the blue **`▶ RUN`** button at the top (or press `Ctrl + Enter` / `Cmd + Enter`).
3. View the query output in the **Query Results** pane at the bottom of the screen.

---

## 🛠️ Step-by-Step Instructions

### Step 1: Execute Automated Lab 1 Provisioning
Instead of running SQL queries manually, run the fully automated Lab 1 setup script. This script will configure BigQuery and securely upload HUMINT PDF reports to Google Cloud Storage.

```bash
cd lab1
chmod +x lab1/setup_lab1.sh
./lab1/code/setup_lab1.sh
```

### Step 2: Verify in BigQuery Studio
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **BigQuery Studio**.
3. Expand your Project ID in the Explorer pane.
4. Verify that all 6 tables and the unified operational view (`v_multi_domain_intelligence`) appear under `learning_labs_mission_data`.

---

## 📜 Dataset Setup SQL Script

```sql
-- Ensure dataset exists
CREATE SCHEMA IF NOT EXISTS `learning_labs_mission_data`
OPTIONS (location = 'US');

--------------------------------------------------------------------------------
-- 1. RADAR TELEMETRY
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.radar_telemetry` (
  track_id STRING,
  timestamp TIMESTAMP,
  latitude FLOAT64,
  longitude FLOAT64,
  altitude_ft INT64,
  velocity_knots INT64,
  bearing_degrees FLOAT64,
  heading_degrees FLOAT64,
  platform_type STRING,
  signature STRING,
  target_id STRING,
  mgrs_coord STRING
);

INSERT INTO `learning_labs_mission_data.radar_telemetry` 
(track_id, timestamp, latitude, longitude, altitude_ft, velocity_knots, bearing_degrees, heading_degrees, platform_type, signature, target_id, mgrs_coord)
VALUES
('TRK-901', CURRENT_TIMESTAMP(), 51.5074, -0.1278, 0, 45, 145.2, 142.0, 'Surface Vessel / Fast Attack Craft', 'Project 22800 Karakurt-Class Guided Missile Corvette', 'TGT-ALPHA-7', '30UGC9914906064'),
('TRK-902', CURRENT_TIMESTAMP(), 51.5174, -0.1178, 32000, 520, 89.5, 268.0, 'Heavy Strategic Aircraft', 'Tu-142 Bear-F / Maritime Reconnaissance Escort', 'TGT-BRAVO-3', '30UGC9914906065'),
('TRK-903', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 51.5300, -0.1000, 15, 25, 12.4, 45.0, 'Mobile Transporter Erector Launcher (TEL)', 'K-300P Bastion-P Mobile Coastal Defense Battery', 'TGT-CHARLIE-9', '30UGC9914906070'),
('TRK-904', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 MINUTE), 51.5000, -0.1300, 1500, 110, 160.0, 180.0, 'Unmanned Aerial System (UAS) Swarm Lead', 'Shahed-136 Autonomous Delta-Wing Drone Formation', 'TGT-DELTA-4', '30UGC9914906060'),
('TRK-905', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 MINUTE), 51.4920, -0.1450, 0, 18, 210.5, 95.0, 'Submersible / Infiltration Craft', 'Autonomous Undersea Vehicle / Special Infiltration Craft', 'TGT-ECHO-1', '30UGC9914906050'),
('TRK-906', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE), 51.5450, -0.0850, 40000, 460, 335.0, 330.0, 'Airborne Early Warning & Control (AEW&C)', 'A-50U Mainstay Battle Management Aircraft', 'TGT-FOXTROT-8', '30UGC9914906085'),
('TRK-907', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE), 51.4800, -0.1550, 250, 480, 75.0, 72.0, 'Low-Altitude Cruise Missile', 'Kh-101 Subsonic Low-Observable Cruise Missile', 'TGT-GOLF-2', '30UGC9914906040'),
('TRK-908', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE), 51.5600, -0.0700, 50, 35, 120.0, 118.0, 'Special Purpose EW Support Vessel', 'Yantar-Class Auxiliary General Intelligence (AGI) Vessel', 'TGT-HOTEL-5', '30UGC9914906090');

--------------------------------------------------------------------------------
-- 2. ELECTRONIC WARFARE (EW) INTERCEPTS
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.ew_intercepts` (
  ew_id STRING,
  timestamp TIMESTAMP,
  sensor_location STRING,
  bearing_degrees FLOAT64,
  ew_bearing FLOAT64,
  signal_frequency_ghz FLOAT64,
  prf_khz FLOAT64,
  emitter_type STRING,
  threat_level STRING,
  signal_strength_dbm FLOAT64,
  estimated_track_id STRING,
  track_id STRING,
  target_id STRING
);

INSERT INTO `learning_labs_mission_data.ew_intercepts`
(ew_id, timestamp, sensor_location, bearing_degrees, ew_bearing, signal_frequency_ghz, prf_khz, emitter_type, threat_level, signal_strength_dbm, estimated_track_id, track_id, target_id)
VALUES
('EW-INT-101', CURRENT_TIMESTAMP(), 'Site-A', 145.2, 145.2, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -68.4, 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-INT-101B', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -74.2, 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-INT-102', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 10.25, 3.20, 'Phazotron Zhuk-M Multi-Mode Airborne Radar', 'HIGH', -62.1, 'TRK-902', 'TRK-902', 'TGT-BRAVO-3'),
('EW-INT-103', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'Site-C', 12.4, 12.4, 2.15, 0.80, 'Monolit-B Coastal Over-The-Horizon Active/Passive Radar', 'CRITICAL', -58.7, 'TRK-903', 'TRK-903', 'TGT-CHARLIE-9'),
('EW-INT-104', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 MINUTE), 'Site-A', 160.0, 160.0, 8.52, 2.10, 'Shahed-136 Encrypted Guidance & Swarm Telemetry', 'HIGH', -71.5, 'TRK-904', 'TRK-904', 'TGT-DELTA-4');

--------------------------------------------------------------------------------
-- 3. SATELLITE RECONNAISSANCE & IMAGERY INTEL
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.satellite_recon` (
  image_id STRING,
  timestamp TIMESTAMP,
  target_id STRING,
  mgrs_coord STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  sensor_type STRING,
  cloud_cover_percentage FLOAT64,
  detected_structures_units STRING,
  confidence_score FLOAT64,
  image_resolution_meters FLOAT64
);

INSERT INTO `learning_labs_mission_data.satellite_recon`
(image_id, timestamp, target_id, mgrs_coord, latitude, longitude, sensor_type, cloud_cover_percentage, detected_structures_units, confidence_score, image_resolution_meters)
VALUES
('SAT-SAR-112', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR), 'TGT-ALPHA-7', '30UGC9914906064', 51.5074, -0.1278, 'SAR', 0.0, 'Fast Attack Craft equipped with 8-cell VLS and AK-176MA naval gun', 0.94, 0.30),
('SAT-EO-998', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR), 'TGT-CHARLIE-9', '30UGC9914906070', 51.5300, -0.1000, 'EO', 12.0, 'K-300P Bastion-P Mobile Missile TEL with support command vehicle deployed in tree line', 0.95, 0.25),
('SAT-SAR-115', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 50 MINUTE), 'TGT-ECHO-1', '30UGC9914906050', 51.4920, -0.1450, 'SAR', 0.0, 'Subsurface wake disturbance consistent with submerged diver delivery vehicle or autonomous underwater vessel near harbor entry', 0.86, 0.30);

--------------------------------------------------------------------------------
-- 4. CYBER THREAT INTELLIGENCE
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.cyber_threat_intel` (
  event_id STRING,
  timestamp TIMESTAMP,
  target_system STRING,
  threat_actor STRING,
  indicator_of_compromise STRING,
  compromised_c2_frequency_mhz FLOAT64,
  affected_tactical_network STRING,
  threat_level STRING,
  status STRING,
  target_id STRING,
  description STRING
);

INSERT INTO `learning_labs_mission_data.cyber_threat_intel`
(event_id, timestamp, target_system, threat_actor, indicator_of_compromise, compromised_c2_frequency_mhz, affected_tactical_network, threat_level, status, target_id, description)
VALUES
('CYB-001', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 MINUTE), 'Site-A_Radar_Control', 'APT-BEAR', 'IP:198.51.100.84', 415.50, 'TACNET-NORTH-COASTAL', 'CRITICAL', 'Active Breach', 'TGT-ALPHA-7', 'Adversary injected spoofed azimuth packets into Site-A coastal radar processing core to mask TRK-901 approach.'),
('CYB-002', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 25 MINUTE), 'Comm-Relay-7_Air_Defense', 'SANDWORM-TEAM', 'Domain: aero-c2-telemetry.mil-spoof.org', 243.00, 'LINK-11-AIR-DEFENSE', 'HIGH', 'Active Breach', 'TGT-BRAVO-3', 'Distributed denial-of-service and DNS poison targeting UHF Guard frequency relay synchronizer.');

--------------------------------------------------------------------------------
-- 5. HUMAN INTELLIGENCE (HUMINT) REPORTS
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.humint_reports` (
  report_id STRING,
  timestamp TIMESTAMP,
  target_id STRING,
  mgrs_coord STRING,
  location_name STRING,
  source_reliability STRING,
  suspected_movement STRING,
  content STRING,
  reported_by STRING
);

INSERT INTO `learning_labs_mission_data.humint_reports`
(report_id, timestamp, target_id, mgrs_coord, location_name, source_reliability, suspected_movement, content, reported_by)
VALUES
('HUM-445', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR), 'TGT-ALPHA-7', '30UGC9914906064', 'Blackwater Estuary Inlet', 'A - Completely Reliable', 'Unauthorized fast attack missile craft maneuvering toward shipping channel under maritime radar cover', 'Local maritime watcher confirms unauthorized fast attack vessel masked as commercial workboat operating out of coastal estuary depot without AIS transponder; observed loading dual containerized anti-ship missile cannisters at midnight.', 'Station Alpha Field Officer');

--------------------------------------------------------------------------------
-- 6. FRIENDLY BLUE FORCE ASSETS (BFT)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `learning_labs_mission_data.friendly_assets` (
  asset_id STRING,
  unit_name STRING,
  asset_type STRING,
  callsign STRING,
  current_status STRING,
  defensive_perimeter STRING,
  assigned_sector STRING,
  mgrs_coord STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  operational_readiness STRING,
  last_beacon_time TIMESTAMP
);

INSERT INTO `learning_labs_mission_data.friendly_assets`
(asset_id, unit_name, asset_type, callsign, current_status, defensive_perimeter, assigned_sector, mgrs_coord, latitude, longitude, operational_readiness, last_beacon_time)
VALUES
('FA-DDG-01', 'HMS Defender (Type 45 Guided Missile Destroyer)', 'Aegis / Sea Viper Air Defense Destroyer', 'SENTINEL-1', 'MISSION READY / WEAPONS FREE', '60nm Sea Viper Aster-30 Air & Missile Defense Envelope', 'SECTOR-NORTH-COASTAL', '30UGC9900005000', 51.4850, -0.1100, '100% Fully Mission Capable', CURRENT_TIMESTAMP()),
('FA-SHORAD-03', '16th Royal Artillery Regiment (NASAMS / Sky Sabre Battery)', 'Short/Medium Range Surface-to-Air Missile Battery', 'SHIELD-3', 'AIR SEARCH ENGAGED / TRACKING ADVERSARY SWARM', '25km NASAMS Engagement Zone / Point Defense Bubble', 'SECTOR-DELTA-EAST', '30UGC9914906060', 51.5000, -0.1300, '90% Mission Capable', CURRENT_TIMESTAMP());

--------------------------------------------------------------------------------
-- 7. UNIFIED OPERATIONAL VIEW
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW `learning_labs_mission_data.v_multi_domain_intelligence` AS
SELECT 
  r.track_id,
  r.target_id,
  r.timestamp as radar_time,
  r.platform_type,
  r.signature as radar_signature,
  r.altitude_ft,
  r.velocity_knots,
  r.mgrs_coord,
  e.ew_id,
  e.emitter_type,
  e.bearing_degrees as ew_bearing,
  e.signal_frequency_ghz,
  e.prf_khz,
  e.threat_level as ew_threat_level,
  s.image_id,
  s.sensor_type as sat_sensor,
  s.detected_structures_units as sat_detection,
  s.confidence_score as sat_confidence,
  c.event_id as cyber_event_id,
  c.threat_actor as cyber_actor,
  c.target_system as cyber_target_system,
  c.status as cyber_status,
  h.report_id as humint_id,
  h.source_reliability as humint_reliability,
  h.content as humint_content,
  f.unit_name as friendly_unit,
  f.callsign as friendly_callsign,
  f.defensive_perimeter as friendly_perimeter
FROM `learning_labs_mission_data.radar_telemetry` r
LEFT JOIN `learning_labs_mission_data.ew_intercepts` e 
  ON r.track_id = e.track_id OR r.target_id = e.target_id
LEFT JOIN `learning_labs_mission_data.satellite_recon` s 
  ON r.target_id = s.target_id
LEFT JOIN `learning_labs_mission_data.cyber_threat_intel` c 
  ON r.target_id = c.target_id
LEFT JOIN `learning_labs_mission_data.humint_reports` h 
  ON r.target_id = h.target_id
LEFT JOIN `learning_labs_mission_data.friendly_assets` f 
  ON r.mgrs_coord = f.mgrs_coord OR (r.track_id = 'TRK-901' AND f.assigned_sector = 'SECTOR-NORTH-COASTAL');
```

---

## 🔍 Guided SQL Queries (BigQuery Studio Hands-On Exercises)

After setting up the dataset, open a **new query tab** in BigQuery Studio and execute each of the guided queries below to practice querying multi-domain intelligence and prove the key architectural learning points:

### Query 1: Radar & EW Sensor Fusion (Multi-Sensor Bearing Alignment)
**Architectural Goal**: Demonstrate multi-sensor spatial and bearing correlation across distinct physical telemetry schemas (`Spec.md §2.1, BAC-01`).
```sql
SELECT 
  r.track_id,
  r.platform_type,
  r.signature AS radar_signature,
  r.bearing_degrees AS radar_bearing,
  e.ew_id,
  e.emitter_type,
  e.signal_frequency_ghz,
  e.bearing_degrees AS ew_bearing,
  e.threat_level
FROM `learning_labs_mission_data.radar_telemetry` r
JOIN `learning_labs_mission_data.ew_intercepts` e
  ON r.track_id = e.track_id
WHERE r.track_id = 'TRK-901'
  AND ABS(r.bearing_degrees - e.bearing_degrees) <= 10.0;
```
* **Proven Learning Point:** Correlating radar kinematics with electronic emitter signatures to eliminate single-sensor ambiguity.
* **Expected Outcome:** Returns a correlated record linking `TRK-901` with the Mineral-ME naval fire control radar (9.41 GHz, PRF 1.65 kHz) on aligned bearing 145.2° with `CRITICAL` threat level.

---

### Query 2: Cyber-Kinetic Convergence (JADC2 Physical-Cyber Fusion)
**Architectural Goal**: Correlate cyber threat intelligence with physical radar track telemetry to detect multi-domain attacks (`Spec.md §2.1`).
```sql
SELECT 
  c.event_id,
  c.threat_actor,
  c.target_system,
  c.status,
  c.description AS cyber_impact,
  r.track_id,
  r.platform_type,
  r.velocity_knots,
  r.mgrs_coord
FROM `learning_labs_mission_data.cyber_threat_intel` c
JOIN `learning_labs_mission_data.radar_telemetry` r
  ON c.target_id = r.target_id
WHERE c.threat_level = 'CRITICAL';
```
* **Proven Learning Point:** Demonstrating JADC2 cyber-physical operational convergence in structured telemetry.
* **Expected Outcome:** Matches `APT-BEAR` breach `CYB-001` on `Site-A_Radar_Control` (spoofing azimuth packets) correlated directly with approaching hostile contact `TRK-901` (`TGT-ALPHA-7`) traveling at 45 knots toward MGRS `30UGC9914906064`.

---

### Query 3: Blue Force Response & Engagement Reachability
**Architectural Goal**: Query friendly asset postures and engagement bubbles against incoming threats (`Spec.md §2.1`).
```sql
SELECT 
  f.asset_id,
  f.unit_name,
  f.callsign,
  f.current_status,
  f.defensive_perimeter,
  f.operational_readiness,
  r.track_id,
  r.platform_type,
  r.velocity_knots
FROM `learning_labs_mission_data.friendly_assets` f
CROSS JOIN `learning_labs_mission_data.radar_telemetry` r
WHERE r.velocity_knots >= 40
  AND f.assigned_sector = 'SECTOR-NORTH-COASTAL';
```
* **Proven Learning Point:** Operational planning and spatial/attribute filtering for defensive posture.
* **Expected Outcome:** Identifies `HMS Defender` (`SENTINEL-1`) with a 60nm Aster-30 Sea Viper missile defense bubble, 100% mission capable to engage high-speed contact `TRK-901` (45 knots).

---

### Query 4: Unified Multi-Domain Common Operational Picture (COP)
**Architectural Goal**: Query the pre-joined view `v_multi_domain_intelligence` to generate a 360-degree target dossier.
```sql
SELECT 
  track_id,
  target_id,
  platform_type,
  radar_signature,
  emitter_type,
  ew_bearing,
  sat_detection,
  sat_confidence,
  cyber_actor,
  cyber_target_system,
  humint_content,
  friendly_unit,
  friendly_perimeter
FROM `learning_labs_mission_data.v_multi_domain_intelligence`
WHERE target_id = 'TGT-ALPHA-7';
```
* **Proven Learning Point:** Querying pre-aggregated view contracts enables sub-second decision making.
* **Expected Outcome:** Returns unified multi-domain view encompassing Radar (`TRK-901`), EW (Mineral-ME), Space (`SAT-SAR-112`), Cyber (`APT-BEAR`), and Blue Force (`HMS Defender`).

---

---

## 🎓 Key Learning Points (Master Study Guide Alignment)

This lab establishes the foundational principles of **The Agentic Data Platform** from the Master Study Guide (Module 3):

### 1. The 4-Layer Agentic Data Platform Blueprint
* **Data Collection (Provisioning):** Multi-modal data ingestion into BigQuery Object Tables and Cloud Storage.
* **Data Storage (Knowledge & Ops Base):** High-performance object storage and analytical databases (BigQuery) for structured operational data.
* **Data Processing (Cognitive Search):** Semantic feature extraction and live data enrichment (to be utilized in subsequent labs).
* **Data Governance (Trust & Control):** Data-to-AI lineage and strict agent data access control (IAM).

### 2. Unifying Unstructured & Structured Data
* **The Architecture:** Modern multi-domain agents require both—semantic vector retrieval for unstructured HUMINT/PDFs and deterministic Text-to-SQL for exact operational metrics (Radar, EW).
* **The Implementation:** This lab provisions the structured relational tier in BigQuery, preparing for hybrid correlation with unstructured GCS assets.

### 3. SQL Pushdown vs. LLM Arithmetic
* **The Antipattern:** Prompting an LLM to compute mathematical bearings, calculate kinetic intercept windows, or filter thousands of raw kinematic rows inside its context window. This wastes tokens, introduces non-deterministic rounding errors, and invites hallucinations.
* **The Best Practice:** Offload all computational, spatial, temporal, and aggregation logic to BigQuery's native, vectorized analytical engine via SQL pushdown. The LLM acts purely as an intent translator, generating parameterized SQL queries and receiving concise, verified numerical results.

### 4. Curated Analytical Views as Hallucination Countermeasures
* **The Challenge:** Expecting an LLM to correctly execute 6-way `JOIN` operations across foreign keys without schema mismatch or join explosion under operational pressure.
* **The Solution:** Exposing curated, pre-joined analytical views (`v_multi_domain_intelligence`). By flattening the relational complexity into an authoritative operational view, we collapse LLM tool execution from multi-hop SQL joins down to single-pass queries, achieving sub-second response times and 100% schema accuracy.

---


## 🎯 Key Takeaways for Downstream AI Agents
In **Lab 2** and **Lab 3**, you will not need to write these SQL queries manually. Instead, your **Gemini 3.8 Flash Agent** (built with ADK 2.0) will interpret your natural language questions, automatically generate and execute these exact SQL queries via **Model Context Protocol (MCP)**, and synthesize real-time mission intelligence dossiers in seconds!


---

## 🚀 System Architecture Improvement Opportunities

While the current data foundation demonstrates core multi-domain intelligence correlation, an enterprise-grade production system could be further hardened and expanded. Below are three architectural improvements to consider:

*   **Google Cloud Architecture Framework (Performance & Cost): BigQuery Materialized Views**
    *   *Improvement:* As the number of concurrent agents and analysts scales, repeatedly scanning and joining the same underlying tables incurs redundant compute costs and latency. Upgrading `v_multi_domain_intelligence` to a BigQuery Materialized View precomputes and caches the join results in the background, guaranteeing millisecond response times for agent tool calls while strictly capping compute costs.
    *   *Reference:* [BigQuery Materialized Views](https://cloud.google.com/bigquery/docs/materialized-views-intro)
*   **Google ADK 2.0: Dynamic Schema via `ToolContext`**
    *   *Improvement:* The current agent relies on a static understanding of the BigQuery schema. By utilizing ADK 2.0's dynamic `ToolContext` injection, the agent can fetch the live BigQuery `INFORMATION_SCHEMA` at runtime and inject it as strongly typed models. If the upstream data schema drifts, the ADK agent automatically adapts its SQL generation without code redeployment.
    *   *Reference:* [Google ADK 2.0 Documentation](https://adk.dev/2.0/)
*   **Broader Google Cloud Capability: BigQuery Geospatial (GIS) Analytics**
    *   *Improvement:* Instead of relying on text-based MGRS strings, implement native BigQuery GIS (`GEOGRAPHY` types). This unlocks spatial functions like `ST_DWithin` and `ST_INTERSECTS`, allowing the agent to execute mathematically perfect spatial queries (e.g., determining exactly which threats have breached a 50km defensive perimeter).
    *   *Reference:* [BigQuery GIS Introduction](https://cloud.google.com/bigquery/docs/gis-intro)
