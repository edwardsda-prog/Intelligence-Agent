-- Mission Intel Mission Intelligence Multi-Domain Dataset Setup
-- Dataset: mission_data
-- Target Project: {PROJECT_ID} (or your active GCP Project ID)
-- Description: Comprehensive multi-domain defense mission intelligence dataset spanning:
--   1. Radar Telemetry (air, surface, littoral, and subsurface tracks)
--   2. Electronic Warfare (EW) Intercepts & Bearings (signals, PRF, emitters, threat levels)
--   3. Satellite Reconnaissance (SAR, EO, IR imagery, detected structures/units, confidence)
--   4. Cyber Threat Intelligence (threat actors, IOCs, compromised C2 frequencies, affected tactical networks)
--   5. Human Intelligence (HUMINT) Reports (source reliability, observer reports, suspected adversary movements)
--   6. Friendly Blue Force Assets (callsigns, readiness, defensive perimeters, assigned sectors)

-- Ensure the dataset exists:
CREATE SCHEMA IF NOT EXISTS `mission_data`
OPTIONS (location = 'us-central1');

--------------------------------------------------------------------------------
-- 1. RADAR TELEMETRY
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.radar_telemetry` (
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

INSERT INTO `mission_data.radar_telemetry` 
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
-- 2. ELECTRONIC WARFARE (EW) INTERCEPTS & BEARINGS
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.ew_intercepts` (
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
  radar_track_id STRING,
  target_id STRING
);

INSERT INTO `mission_data.ew_intercepts`
(ew_id, timestamp, sensor_location, bearing_degrees, ew_bearing, signal_frequency_ghz, prf_khz, emitter_type, threat_level, signal_strength_dbm, estimated_track_id, track_id, radar_track_id, target_id)
VALUES
('EW-INT-101', CURRENT_TIMESTAMP(), 'Site-A', 145.2, 145.2, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -68.4, 'TRK-901', 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-INT-101B', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -74.2, 'TRK-901', 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-INT-102', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 10.25, 3.20, 'Phazotron Zhuk-M Multi-Mode Airborne Radar', 'HIGH', -62.1, 'TRK-902', 'TRK-902', 'TRK-902', 'TGT-BRAVO-3'),
('EW-INT-103', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'Site-C', 12.4, 12.4, 2.15, 0.80, 'Monolit-B Coastal Over-The-Horizon Active/Passive Radar', 'CRITICAL', -58.7, 'TRK-903', 'TRK-903', 'TRK-903', 'TGT-CHARLIE-9'),
('EW-INT-104', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 MINUTE), 'Site-A', 160.0, 160.0, 8.52, 2.10, 'Shahed-136 Encrypted Guidance & Swarm Telemetry', 'HIGH', -71.5, 'TRK-904', 'TRK-904', 'TRK-904', 'TGT-DELTA-4'),
('EW-INT-105', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 MINUTE), 'Site-D', 210.5, 210.5, 1.42, 0.45, 'Burst Data Satellite Link & Acoustic Transponder Relay', 'MEDIUM', -83.0, 'TRK-905', 'TRK-905', 'TRK-905', 'TGT-ECHO-1'),
('EW-INT-106', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE), 'Site-C', 335.0, 335.0, 3.10, 1.20, 'Shmel-M Airborne Early Warning Surveillance Radar', 'HIGH', -55.3, 'TRK-906', 'TRK-906', 'TRK-906', 'TGT-FOXTROT-8'),
('EW-INT-107', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE), 'Site-A', 75.0, 75.0, 14.80, 4.50, 'Otklik Active Millimeter Terminal Guidance Seeker', 'CRITICAL', -49.8, 'TRK-907', 'TRK-907', 'TRK-907', 'TGT-GOLF-2'),
('EW-INT-108', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE), 'Site-E', 120.0, 120.0, 4.85, 1.95, 'Krasukha-4 Tactical Broadband Jamming System', 'HIGH', -52.0, 'TRK-908', 'TRK-908', 'TRK-908', 'TGT-HOTEL-5');

-- Dedicated ew_bearings table for backwards compatibility
CREATE OR REPLACE TABLE `mission_data.ew_bearings` (
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
  radar_track_id STRING,
  target_id STRING
);

INSERT INTO `mission_data.ew_bearings`
(ew_id, timestamp, sensor_location, bearing_degrees, ew_bearing, signal_frequency_ghz, prf_khz, emitter_type, threat_level, signal_strength_dbm, estimated_track_id, track_id, radar_track_id, target_id)
VALUES
('EW-001', CURRENT_TIMESTAMP(), 'Site-A', 145.2, 145.2, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -68.4, 'TRK-901', 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-002', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 9.41, 1.65, 'Mineral-ME Naval Target Acquisition & Fire Control', 'CRITICAL', -74.2, 'TRK-901', 'TRK-901', 'TRK-901', 'TGT-ALPHA-7'),
('EW-003', CURRENT_TIMESTAMP(), 'Site-B', 89.5, 89.5, 10.25, 3.20, 'Phazotron Zhuk-M Multi-Mode Airborne Radar', 'HIGH', -62.1, 'TRK-902', 'TRK-902', 'TRK-902', 'TGT-BRAVO-3'),
('EW-004', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'Site-C', 12.4, 12.4, 2.15, 0.80, 'Monolit-B Coastal Over-The-Horizon Active/Passive Radar', 'CRITICAL', -58.7, 'TRK-903', 'TRK-903', 'TRK-903', 'TGT-CHARLIE-9'),
('EW-005', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 MINUTE), 'Site-A', 160.0, 160.0, 8.52, 2.10, 'Shahed-136 Encrypted Guidance & Swarm Telemetry', 'HIGH', -71.5, 'TRK-904', 'TRK-904', 'TRK-904', 'TGT-DELTA-4'),
('EW-006', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 MINUTE), 'Site-D', 210.5, 210.5, 1.42, 0.45, 'Burst Data Satellite Link & Acoustic Transponder Relay', 'MEDIUM', -83.0, 'TRK-905', 'TRK-905', 'TRK-905', 'TGT-ECHO-1'),
('EW-007', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE), 'Site-C', 335.0, 335.0, 3.10, 1.20, 'Shmel-M Airborne Early Warning Surveillance Radar', 'HIGH', -55.3, 'TRK-906', 'TRK-906', 'TRK-906', 'TGT-FOXTROT-8'),
('EW-008', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE), 'Site-A', 75.0, 75.0, 14.80, 4.50, 'Otklik Active Millimeter Terminal Guidance Seeker', 'CRITICAL', -49.8, 'TRK-907', 'TRK-907', 'TRK-907', 'TGT-GOLF-2'),
('EW-009', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE), 'Site-E', 120.0, 120.0, 4.85, 1.95, 'Krasukha-4 Tactical Broadband Jamming System', 'HIGH', -52.0, 'TRK-908', 'TRK-908', 'TRK-908', 'TGT-HOTEL-5');

--------------------------------------------------------------------------------
-- 3. SATELLITE RECONNAISSANCE & IMAGERY INTEL
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.satellite_recon` (
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

INSERT INTO `mission_data.satellite_recon`
(image_id, timestamp, target_id, mgrs_coord, latitude, longitude, sensor_type, cloud_cover_percentage, detected_structures_units, confidence_score, image_resolution_meters)
VALUES
('SAT-SAR-112', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR), 'TGT-ALPHA-7', '30UGC9914906064', 51.5074, -0.1278, 'SAR', 0.0, 'Fast Attack Craft equipped with 8-cell VLS and AK-176MA naval gun', 0.94, 0.30),
('SAT-SAR-113', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE), 'TGT-BRAVO-3', '30UGC9914906065', 51.5174, -0.1178, 'SAR', 0.0, 'Twin-engine swept-wing heavy aircraft in holding pattern, ECM pods deployed', 0.88, 0.50),
('SAT-EO-998', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR), 'TGT-CHARLIE-9', '30UGC9914906070', 51.5300, -0.1000, 'EO', 12.0, 'K-300P Bastion-P Mobile Missile TEL with support command vehicle deployed in tree line', 0.95, 0.25),
('SAT-EO-1002', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'TGT-DELTA-4', '30UGC9914906060', 51.5000, -0.1300, 'EO/IR', 5.0, 'Low-altitude delta-wing drone swarm flying in tactical wedge formation', 0.91, 0.30),
('SAT-SAR-115', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 50 MINUTE), 'TGT-ECHO-1', '30UGC9914906050', 51.4920, -0.1450, 'SAR', 0.0, 'Subsurface wake disturbance consistent with submerged diver delivery vehicle or autonomous underwater vessel near harbor entry', 0.86, 0.30),
('SAT-EO-1015', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 40 MINUTE), 'TGT-FOXTROT-8', '30UGC9914906085', 51.5450, -0.0850, 'EO', 8.0, 'A-50U Mainstay airborne command platform with rotodome antenna rotating', 0.96, 0.40),
('SAT-IR-402', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 MINUTE), 'TGT-GOLF-2', '30UGC9914906040', 51.4800, -0.1550, 'IR', 3.0, 'Thermal plume and airframe signature of low-flying subsonic cruise missile skimming terrain', 0.93, 0.50),
('SAT-SAR-120', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 70 MINUTE), 'TGT-HOTEL-5', '30UGC9914906090', 51.5600, -0.0700, 'SAR', 0.0, 'Yantar-class intelligence collection ship with high-power satellite antennas and sub-sea deployment cranes active', 0.92, 0.30);

-- Dedicated satellite_imagery_intel table for backwards compatibility
CREATE OR REPLACE TABLE `mission_data.satellite_imagery_intel` (
  image_id STRING,
  timestamp TIMESTAMP,
  target_id STRING,
  mgrs_coord STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  sensor_type STRING,
  cloud_cover_percentage FLOAT64,
  confidence_score FLOAT64,
  detected_object STRING
);

INSERT INTO `mission_data.satellite_imagery_intel`
(image_id, timestamp, target_id, mgrs_coord, latitude, longitude, sensor_type, cloud_cover_percentage, confidence_score, detected_object)
VALUES
('SAT-SAR-112', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR), 'TGT-ALPHA-7', '30UGC9914906064', 51.5074, -0.1278, 'SAR', 0.0, 0.94, 'Fast Attack Craft equipped with 8-cell VLS and AK-176MA naval gun'),
('SAT-SAR-113', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE), 'TGT-BRAVO-3', '30UGC9914906065', 51.5174, -0.1178, 'SAR', 0.0, 0.88, 'Twin-engine swept-wing heavy aircraft in holding pattern, ECM pods deployed'),
('SAT-EO-998', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR), 'TGT-CHARLIE-9', '30UGC9914906070', 51.5300, -0.1000, 'EO', 12.0, 0.95, 'K-300P Bastion-P Mobile Missile TEL with support command vehicle deployed in tree line'),
('SAT-EO-1002', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'TGT-DELTA-4', '30UGC9914906060', 51.5000, -0.1300, 'EO/IR', 5.0, 0.91, 'Low-altitude delta-wing drone swarm flying in tactical wedge formation'),
('SAT-SAR-115', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 50 MINUTE), 'TGT-ECHO-1', '30UGC9914906050', 51.4920, -0.1450, 'SAR', 0.0, 0.86, 'Subsurface wake disturbance consistent with submerged diver delivery vehicle or autonomous underwater vessel near harbor entry'),
('SAT-EO-1015', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 40 MINUTE), 'TGT-FOXTROT-8', '30UGC9914906085', 51.5450, -0.0850, 'EO', 8.0, 0.96, 'A-50U Mainstay airborne command platform with rotodome antenna rotating'),
('SAT-IR-402', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 MINUTE), 'TGT-GOLF-2', '30UGC9914906040', 51.4800, -0.1550, 'IR', 3.0, 0.93, 'Thermal plume and airframe signature of low-flying subsonic cruise missile skimming terrain'),
('SAT-SAR-120', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 70 MINUTE), 'TGT-HOTEL-5', '30UGC9914906090', 51.5600, -0.0700, 'SAR', 0.0, 0.92, 'Yantar-class intelligence collection ship with high-power satellite antennas and sub-sea deployment cranes active');

--------------------------------------------------------------------------------
-- 4. CYBER THREAT INTELLIGENCE
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.cyber_threat_intel` (
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

INSERT INTO `mission_data.cyber_threat_intel`
(event_id, timestamp, target_system, threat_actor, indicator_of_compromise, compromised_c2_frequency_mhz, affected_tactical_network, threat_level, status, target_id, description)
VALUES
('CYB-001', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 MINUTE), 'Site-A_Radar_Control', 'APT-BEAR', 'IP:198.51.100.84', 415.50, 'TACNET-NORTH-COASTAL', 'CRITICAL', 'Active Breach', 'TGT-ALPHA-7', 'Adversary injected spoofed azimuth packets into Site-A coastal radar processing core to mask TRK-901 approach.'),
('CYB-002', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 25 MINUTE), 'Comm-Relay-7_Air_Defense', 'SANDWORM-TEAM', 'Domain: aero-c2-telemetry.mil-spoof.org', 243.00, 'LINK-11-AIR-DEFENSE', 'HIGH', 'Active Breach', 'TGT-BRAVO-3', 'Distributed denial-of-service and DNS poison targeting UHF Guard frequency relay synchronizer.'),
('CYB-003', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR), 'Site-C_EW_Array_Firmware', 'APT-BEAR', 'SHA256: 8f3a2b7c4d1e9f02384a28bb0194857c91e', 312.80, 'COASTAL-DEF-RADNET', 'HIGH', 'Isolated', 'TGT-CHARLIE-9', 'Malicious rootkit firmware flashing attempt detected on coastal passive RF listener array.'),
('CYB-004', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 MINUTE), 'Tactical_Data_Network_Gateway_4', 'VOODOO-BEAR', 'IP:203.0.113.195', 433.92, 'TACNET-UAS-DEFENSE', 'HIGH', 'Active Breach', 'TGT-DELTA-4', 'RF telemetry replay attack injecting ghost UAS tracks to overwhelm automated C-UAS fire control.'),
('CYB-005', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE), 'Port_Maritime_Traffic_VTS', 'APT-BEAR', 'IP:198.51.100.220', 156.80, 'PORT-SEC-NET', 'MEDIUM', 'Contained', 'TGT-ECHO-1', 'Vessel Traffic Service transponder receiver blinded via unauthorized SSH lateral movement.'),
('CYB-006', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 45 MINUTE), 'Joint_Tactical_Air_Operations_Center', 'COZY-BEAR', 'Malicious C2 Payload / CVE-2026-4112', 960.50, 'LINK-16-TACTICAL', 'CRITICAL', 'Investigating', 'TGT-FOXTROT-8', 'Credential harvesting attempt against Link-16 crypto key distribution workstation.'),
('CYB-007', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE), 'Coastal_Surveillance_Fiber_Hub', 'APT-29', 'BGP Route Hijack / AS65001', 225.40, 'COASTAL-RADAR-FIBER', 'HIGH', 'Blocked', 'TGT-GOLF-2', 'Autonomous system route manipulation intended to divert optical sensor telemetry to external sinkhole.'),
('CYB-008', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 80 MINUTE), 'Electronic_Warfare_Control_Node_East', 'FANCY-BEAR', 'IP:192.168.100.44', 385.20, 'AIR-CORRIDOR-LINK', 'MEDIUM', 'Mitigated', 'TGT-HOTEL-5', 'Unauthorized credential stuffing targeting tactical gateway router.');

--------------------------------------------------------------------------------
-- 5. HUMAN INTELLIGENCE (HUMINT) REPORTS
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.humint_reports` (
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

INSERT INTO `mission_data.humint_reports`
(report_id, timestamp, target_id, mgrs_coord, location_name, source_reliability, suspected_movement, content, reported_by)
VALUES
('HUM-445', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR), 'TGT-ALPHA-7', '30UGC9914906064', 'Blackwater Estuary Inlet', 'A - Completely Reliable', 'Unauthorized fast attack missile craft maneuvering toward shipping channel under maritime radar cover', 'Local maritime watcher confirms unauthorized fast attack vessel masked as commercial workboat operating out of coastal estuary depot without AIS transponder; observed loading dual containerized anti-ship missile cannisters at midnight.', 'Station Alpha Field Officer'),
('HUM-446', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 12 HOUR), 'TGT-BRAVO-3', '30UGC9914906065', 'Farnborough Outer Corridor', 'B - Usually Reliable', 'Adversary heavy bomber route staging with mobile satellite uplink escort', 'Signals liaison informant observed mobile SATCOM vehicle deploying mast array coincident with scheduled high-altitude strategic flight route rehearsal.', 'Signals Liaison Detachment'),
('HUM-447', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY), 'TGT-CHARLIE-9', '30UGC9914906070', 'Thetford Forest Clearing', 'A - Completely Reliable', 'Convoy of 8x8 heavy TEL transporter vehicles deploying under multispectral camouflage netting', 'Border observer reports convoy of heavy multi-axle missile transporter erector launchers entering concealed forestry clearing; vehicle silhouettes match K-300 Bastion battery components.', 'Border Surveillance Unit 4'),
('HUM-448', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 HOUR), 'TGT-DELTA-4', '30UGC9914906060', 'Harwich Industrial Wharf', 'C - Fairly Reliable', 'Drone swarm catapult assembly and pre-flight battery charging in warehouse district', 'Warehouse worker reports suspicious shipping crates labeled farm equipment containing delta-wing unmanned airframes and rocket assist booster brackets.', 'Port Watcher Team'),
('HUM-449', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR), 'TGT-ECHO-1', '30UGC9914906050', 'Felixstowe Outer Anchorage', 'B - Usually Reliable', 'Uncrewed diver delivery vehicle / midget sub launched from cargo vessel Baltic Trader', 'Tugboat deckhand observed submerged craft deployment from stern crane of merchant ship anchored 3nm offshore under low-light conditions.', 'Maritime Intelligence Unit'),
('HUM-450', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 50 MINUTE), 'TGT-FOXTROT-8', '30UGC9914906085', 'Colchester Communications Node', 'A - Completely Reliable', 'Mobile electronic jamming van deploying collapsible parabolic antenna array', 'Patrol spotted unmarked communication surveillance vehicle with roof-mounted radome operating adjacent to military fiber relay.', 'Special Reconnaissance Unit 2'),
('HUM-451', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR), 'TGT-GOLF-2', '30UGC9914906040', 'Thames Estuary Sea Reach', 'B - Usually Reliable', 'Air-launched cruise missile decoy trajectory verification rehearsal', 'Maritime observer spotted low-altitude high-speed projectile skimming low over sandbanks before turning toward open waters.', 'Coastal Observer Corps'),
('HUM-452', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 HOUR), 'TGT-HOTEL-5', '30UGC9914906090', 'Lowestoft Maritime Approaches', 'C - Fairly Reliable', 'Infiltration scout team monitoring allied radar blind angles', 'Fishermen reported non-responsive foreign survey vessel dropping acoustic hydrophone cables near submarine power interconnector.', 'Regional Informant Network');

--------------------------------------------------------------------------------
-- 6. FRIENDLY BLUE FORCE ASSETS (BFT)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE `mission_data.friendly_assets` (
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

INSERT INTO `mission_data.friendly_assets`
(asset_id, unit_name, asset_type, callsign, current_status, defensive_perimeter, assigned_sector, mgrs_coord, latitude, longitude, operational_readiness, last_beacon_time)
VALUES
('FA-DDG-01', 'HMS Defender (Type 45 Guided Missile Destroyer)', 'Aegis / Sea Viper Air Defense Destroyer', 'SENTINEL-1', 'MISSION READY / WEAPONS FREE', '60nm Sea Viper Aster-30 Air & Missile Defense Envelope', 'SECTOR-NORTH-COASTAL', '30UGC9900005000', 51.4850, -0.1100, '100% Fully Mission Capable', CURRENT_TIMESTAMP()),
('FA-CAP-04', '11 Squadron RAF (F-35A Lightning II Flight)', 'Stealth Multi-Role Fighter Interceptor', 'VIPER-41', 'AIRBORNE INTERCEPT / COMBAT AIR PATROL', '40nm Meteor / AMRAAM Beyond-Visual-Range Engagement Zone', 'SECTOR-AIR-CAP-BRAVO', '30UGC9914906065', 51.5174, -0.1178, '95% Mission Capable', CURRENT_TIMESTAMP()),
('FA-RECON-02', '13 Squadron RAF (MQ-9A Reaper ISR Flight)', 'Unmanned Reconnaissance / Strike Platform', 'GHOST-07', 'ON STATION / CONTINUOUS ISR ORBIT', '15nm Multi-Spectral Sensor Sweep Coverage Radius', 'SECTOR-RECON-CHARLIE', '30UGC9914906070', 51.5300, -0.1000, '100% Fully Mission Capable', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)),
('FA-SHORAD-03', '16th Royal Artillery Regiment (NASAMS / Sky Sabre Battery)', 'Short/Medium Range Surface-to-Air Missile Battery', 'SHIELD-3', 'AIR SEARCH ENGAGED / TRACKING ADVERSARY SWARM', '25km NASAMS Engagement Zone / Point Defense Bubble', 'SECTOR-DELTA-EAST', '30UGC9914906060', 51.5000, -0.1300, '90% Mission Capable', CURRENT_TIMESTAMP()),
('FA-PATROL-05', 'HMS Trent (Batch 2 River-class Offshore Patrol Vessel)', 'Littoral Patrol Vessel', 'TRIDENT-12', 'INTERCEPTING / MARITIME INTERDICTION PATROL', '10nm Rapid Reaction Littoral Interdiction Zone', 'SECTOR-PORT-APPROACH', '30UGC9914906050', 51.4920, -0.1450, '100% Fully Mission Capable', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 MINUTE)),
('FA-SAM-06', '7 Air Defence Group (Patriot PAC-3 Missile Battery)', 'Long-Range Air and Missile Defense System', 'IRON-WALL-6', 'COMBAT READY / RADAR ACTIVE', '70km PAC-3 Missile Intercept Perimeter', 'SECTOR-AIR-DEFENSE-HUB', '30UGC9850007500', 51.5500, -0.1800, '95% Mission Capable', CURRENT_TIMESTAMP()),
('FA-EW-07', '21 Signal Regiment (Tactical EW / Counter-C2 Detachment)', 'Ground-Based Electronic Warfare & Signals Intercept Node', 'SILENT-HAWK', 'ACTIVE JAMMING / COUNTER-MEASURES LIVE', '35km Directed RF Jamming / Tactical Denial Corridor', 'SECTOR-EW-JAMMING-CORRIDOR', '30UGC9910006200', 51.5100, -0.0900, '100% Fully Mission Capable', CURRENT_TIMESTAMP()),
('FA-SSN-08', 'HMS Astute (Astute-class Nuclear Attack Submarine)', 'Fast Attack Nuclear Submarine', 'DEEP-HUNTER', 'SUBMERGED PATROL / PASSIVE ACOUSTIC TRACKING', '45nm Undersea Acoustic Sensor & Spearfish Torpedo Engagement Bubble', 'SECTOR-SUB-PATROL-ALPHA', '30UGC9940005500', 51.4700, -0.0800, '100% Fully Mission Capable', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 20 MINUTE));

--------------------------------------------------------------------------------
-- 7. UNIFIED OPERATIONAL VIEW FOR ACCELERATED AGENTIC FUSION
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW `mission_data.v_multi_domain_intelligence` AS
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
FROM `mission_data.radar_telemetry` r
LEFT JOIN `mission_data.ew_intercepts` e 
  ON r.track_id = e.estimated_track_id OR r.target_id = e.target_id
LEFT JOIN `mission_data.satellite_recon` s 
  ON r.target_id = s.target_id
LEFT JOIN `mission_data.cyber_threat_intel` c 
  ON r.target_id = c.target_id
LEFT JOIN `mission_data.humint_reports` h 
  ON r.target_id = h.target_id
LEFT JOIN `mission_data.friendly_assets` f 
  ON r.mgrs_coord = f.mgrs_coord OR (r.track_id = 'TRK-901' AND f.assigned_sector = 'SECTOR-NORTH-COASTAL');
