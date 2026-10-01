# Executive Storyboard & Instructor Delivery Playbook
## *Project OP-SENTINEL: Building Governed Multi-Domain Mission Intelligence Agents on Google Cloud*
**Security Classification:** Demonstrator  
**Target Audience:** UK Ministry of Defence (MOD) Joint Forces Command, Defence Digital, Allied Coalition Leadership, and Lead AI/ML Defence Engineers  
**Methodology:** Google Cloud Well-Architected Framework (WAF) for AI/ML Operational Excellence  

---

## 🎯 Executive Overview & Operational Narrative Arc

### The Strategic Mission Scenario
In the contested **Blackwater Estuary Littoral Corridor**, Joint Force Command faces an escalating, hybrid multi-domain threat vector. Near-peer adversaries deploy coordinated surface combatants, supersonic maritime strike aircraft, mobile coastal defense cruise missile (CDCM) transporter-erector-launchers (TELs), autonomous electronic warfare (EW) jammers, and cyber-spoofing vectors against blue force communications.

### The Operational Challenge: Fragmented Data Siloes
Traditionally, sensor telemetry, electronic signals, satellite overhead passes, cyber indicators of compromise (IOCs), and classified field reports reside in isolated security compartments across disconnected command networks. Correlating these multi-domain signals manually requires hours or days of high-stress human analysis—creating critical decision latency during time-sensitive operations.

### The Solution: Governed Multi-Domain Intelligence Ecosystem
Over seven progressive acts, defence engineers and commanders construct, deploy, secure, benchmark, and federate **Project OP-SENTINEL**—a production-grade, secure Agentic AI ecosystem powered by Google Cloud foundation models (Gemini Flash/Pro) and the **Google Agent Developer Kit (ADK 2.0)**. 

```
                                  MISSION INTEL DELIVERY LIFECYCLE
                                  
 [ ACT 1: DATA FOUNDATION ] ──► [ ACT 2: LOCAL PROTOTYPING ] ──► [ ACT 3: ENTERPRISE CLOUD ] ──► [ ACT 4: OPSEC & GUARDRAILS ]
   BigQuery Multi-Domain          ADK 2.0 ReAct Reasoning         Cloud Run MCP Microservice        Model Armor & Cloud DLP
   Sensor Fusion & COP View       Fast-Path & Schema Recovery     Vertex AI Dual-Telemetry Logs     HITL Cryptographic Gates
                                                                                 │
                                                                                 ▼
 [ ACT 7: COALITION A2A ] ◄─── [ ACT 6: OFFLINE EVALUATION ] ◄─── [ ACT 5: MULTIMODAL RAG ]
   Agent Gateway Federation       Vertex AI EvalTask Benchmark    Discovery Engine OCR & Search
   NATO Releasability Caveats     7 Enterprise Quality Dims       Server-Side Context Caching
```

---

## ⏱️ Workshop Operational Timing & Curriculum Breakdown

Detailed schedule options and modular formats are published in [WORKSHOP_SCHEDULE.md](WORKSHOP_SCHEDULE.md).

| Lab / Workshop Phase | Focus & Key Technologies | Automated Setup Time | Customer Guide Reading | Prompt Execution & Verification | Customer Q&A & Discussion | Total Duration |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Phase 0: Pre-Flight Bootstrap** | CloudShell setup, API enablement, environment bootstrap (`setup.sh`) | **3 min** | **5 min** | **2 min** | **5 min** | **15 min** |
| **Lab 1: Analytical Foundations** | BigQuery Studio, 6-table multi-domain schema, unified COP SQL queries | **2 min** | **10 min** | **10 min** | **5 min** | **27 min** |
| **Lab 2: Local ADK 2.0 & ReAct** | Local prototyping, SQLite sandbox, Gemini 3.8 Flash, Fast-Path Intercepts, `adk web` | **1 min** | **10 min** | **10 min** | **5 min** | **26 min** |
| **Lab 3: Decoupled Tools & Cloud Run** | Cloud Run MCP server, Agent Registry, Vertex AI Reasoning Engine, Dual-OTel | **5 min** | **12 min** | **15 min** | **8 min** | **40 min** |
| **Lab 4: OPSEC & Secure Guardrails** | Cloud Model Armor, Cloud DLP MGRS redaction, Human-in-the-Loop (`AUTH_<HASH>`) | **3 min** | **12 min** | **12 min** | **8 min** | **35 min** |
| **Lab 5: Multimodal RAG & Caching** | Discovery Engine OCR datastore, 10 HUMINT PDFs, `#page=N` citations, Context Caching | **5 min** | **12 min** | **15 min** | **8 min** | **40 min** |
| **Lab 6: Offline Benchmark Evaluation** | Golden eval dataset, 7 quality dimensions, quantitative precision, regression CI/CD | **1 min** | **8 min** | **10 min** | **7 min** | **26 min** |
| **Lab 7: Coalition A2A Federation** | Agent-to-Agent protocol, Agent Gateway egress, secure cross-domain defense | **3 min** | **12 min** | **15 min** | **10 min** | **40 min** |
| **Workshop Debrief & Wrap-Up** | Architecture recap, WAF best practices, operational deployment pathways | — | — | — | **15 min** | **15 min** |
| **TOTAL WORKSHOP PROGRAM** | **Complete End-to-End Enterprise Demonstrator Curriculum** | **23 min** | **81 min** | **89 min** | **71 min** | **264 min (~4.5 hrs)** |

> [!NOTE]
> - **Self-Paced Execution**: Individual advanced customers can fast-forward automated setup scripts and complete the 7 labs in **~3 to 3.5 hours**.
> - **Instructor-Led Cohorts**: With group discussions, console inspections, and interactive Q&A, the recommended scheduling window is **1 full day (half-day morning: Labs 1–3; afternoon: Labs 4–7)** or **two 2.5-hour sessions**.

---

## 🎬 Act 1: The Multi-Domain Data Foundation (Lab 1)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** Joint Command is flooded with disparate sensor telemetry across land, sea, air, space, cyber, and human domains in Sector Alpha.
* **The Friction:** Radar detects high-speed track `TRK-901`, EW intercepts a 9.41 GHz radar emitter `EW-501`, IMINT satellite SAR pass `SAT-SAR-112` identifies a missile corvette, cyber alarms flag frequency hopping, and field report `HUM-445` warns of midnight missile loading. No unified operational picture exists to correlate these feeds in real time.
* **The Mission:** Establish a robust analytical data foundation that unifies multi-domain feeds along shared track identifiers and target coordinates without altering raw source data.

### 🎙️ Instructor Hook & Delivery Messaging
> *"Before an AI agent can reason, it must have an authoritative truth to reason over. In military operations, data is noisy, multi-modal, and fragmented across stovepiped services. In this lab, we build the structured Common Operational Picture (COP) in BigQuery that underpins all downstream agentic intelligence."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Reliability & Performance Efficiency*
* **Architectural Pattern:** Star-schema multi-domain data warehousing with analytical view pre-joins (`v_multi_domain_intelligence`).
* **Technology Stack:** Google Cloud BigQuery, partitioned relational schemas, SQL analytical views.

### 💡 Hands-On Customer Experience & Key Milestones
1. Provision BigQuery dataset `learning_labs_mission_data`.
2. Populate six relational tables: `radar_telemetry`, `ew_intercepts`, `satellite_recon`, `cyber_threat_intel`, `humint_reports`, and `friendly_assets`.
3. Construct the unifying analytical view `v_multi_domain_intelligence`.
4. **Customer "Aha!" Moment:** Running a single SQL query that instantly correlates maritime track `TRK-901` with EW emitter `EW-501` and satellite target `TGT-ALPHA-7`, achieving in milliseconds what previously required cross-departmental phone calls.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Emphasize that `v_multi_domain_intelligence` preserves raw sensor lineage while providing the AI agent with a clean, low-latency join key (`track_id` / `target_id`).
* **Common Customer Trap:** Ensure customers set their environment variable `PROJECT_ID` before running `./lab1/setup_lab1.sh` to prevent BigQuery dataset creation under incorrect project scopes.

### 🎯 Key Takeaway & Transition Bridge
> *"High-speed AI agents require a structured, multi-domain analytical data foundation."*  
> **Transition to Lab 2:** Now that the data foundation is solid, how do we equip an LLM to autonomously inspect and query this data without writing manual SQL?

---

## 🎬 Act 2: Local Cognitive Prototyping with ADK & Web UI (Lab 2)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** Software engineers within the Defence Industrial Base (DIB) must build an autonomous reasoning agent that translates natural-language tactical queries from command staff into structured database investigations.
* **The Friction:** Deploying directly to cloud production for every prompt iteration is slow, costly, and difficult to debug. Developers need a sandboxed local environment to inspect reasoning steps, tool calling loops, and edge-case handling.
* **The Mission:** Prototype an intelligent ADK agent locally using a lightweight SQLite replica, test conversational reasoning in the browser, and implement defensive schema recovery and deterministic fast-path routing.

### 🎙️ Instructor Hook & Delivery Messaging
> *"Agentic AI is fundamentally different from a standard chatbot. It does not simply generate text; it plans, executes tools, inspects results, and self-corrects. In this lab, you experience the inner loop of the Google Agent Developer Kit (ADK 2.0) on your local workstation before deploying a single container to the cloud."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Cost Optimization & Operational Excellence*
* **Architectural Pattern:** 
  1. *Dual-Engine Routing / Fast-Path Intercepts:* Deterministic pattern matching resolves routine operational queries (greetings, readiness pings) in $< 50\text{ ms}$ with 0 LLM token spend.
  2. *Autonomous ReAct Self-Correction:* Agent catches SQL exceptions, reflects on table schema definitions, and re-issues corrected queries without crashing.
  3. *Model Right-Sizing:* Selecting low-latency Flash models (Gemini 3.8 Flash: `gemini-3.8-flash`) with low thinking level (`thinking_level="LOW"`) for high-throughput tactical tool orchestration.
* **Technology Stack:** Google ADK 2.0 (`pip install google-adk`), SQLite sandbox, Gemini 3.8 Flash.

### 💡 Hands-On Customer Experience & Key Milestones
1. Initialize local SQLite database `mission_intel_local.db` mirroring the BigQuery schema.
2. Develop `agent.py` defining custom Python tools (`query_local_intelligence`, `list_local_tables`).
3. Launch the visual **ADK Web UI** (`adk web ./`) and interact with the agent in the browser.
4. **Customer "Aha!" Moment:** Intentionally querying a non-existent column and watching the agent in the visual trace view catch the error, inspect the schema, formulate a corrected SQL query, and deliver the answer seamlessly.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Walk customers through the ADK visual trace timeline. Point out the exact demarcation between *Thought*, *Action (Tool Call)*, *Observation (Tool Return)*, and *Final Response*.
* **Common Customer Trap:** Ensure customers do not commit API keys or hardcode paths; the local sandbox should utilize standard ADC credentials (`gcloud auth login --update-adc`).

### 🎯 Key Takeaway & Transition Bridge
> *"ADK enables rapid local agent prototyping, tool definition, and visual trace debugging before pushing to cloud production."*  
> **Transition to Lab 3:** Local sandboxes are great for development, but enterprise command operations demand decoupled cloud microservices, centralized tool governance, and production observability.

---

## 🎬 Act 3: Enterprise Cloud Deployment, MCP & Dual Telemetry (Lab 3)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** The agent prototype must transition to enterprise cloud deployment to serve tactical operations across Joint Force Command.
* **The Friction:** Monolithic agents that embed database credentials directly in the LLM runtime violate Zero-Trust principles. Furthermore, defense SRE teams cannot support production AI systems without full auditability: both distributed trace latency and un-elided prompt/response audit logs are mandatory.
* **The Mission:** Decouple database access into an independent Model Context Protocol (MCP) microservice on Cloud Run, register the tool in Agent Registry, deploy the agent to Vertex AI Reasoning Engine, and enforce dual-telemetry observability.

### 🎙️ Instructor Hook & Delivery Messaging
> *"In production military systems, you never hand an AI agent raw database credentials. You expose governed capabilities through standard protocols. By implementing the Model Context Protocol (MCP) and Vertex AI Reasoning Engine, we achieve complete architectural decoupling, circuit breaker resilience, and deep telemetry visibility."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Operational Excellence & Reliability*
* **Architectural Pattern:** 
  1. *Decoupled Tool Sandboxing:* Model Context Protocol (MCP) deployed on Cloud Run, registered in Agent Registry.
  2. *Resilient Invocation:* Exponential backoff retries and 3-state Circuit Breakers (`CLOSED`, `OPEN`, `HALF_OPEN`).
  3. *Dual-Telemetry Invariant:* Mandatory concurrent activation of:
     - OpenTelemetry spans and metrics (`aiplatform.googleapis.com/reasoning_engine_execution`).
     - Prompt and response audit logging (`aiplatform.googleapis.com/reasoning_engine_model_input_output`) without content elision.
* **Technology Stack:** Cloud Run, Model Context Protocol (MCP), Vertex AI Reasoning Engine, Google Cloud Trace, Cloud Logging.

### 💡 Hands-On Customer Experience & Key Milestones
1. Containerize and deploy the BigQuery MCP server to **Cloud Run** (`lab3/setup_mcp.sh`).
2. Package the reasoning agent (`my_agent`) with explicit `.agent_engine_config.json` and `.env` telemetry flags.
3. Deploy to **Vertex AI Reasoning Engine** (`reasoning_engines.create`) and test live queries.
4. Review Gemini Enterprise Web UI integration guidelines (with customer licensing placeholder).
5. **Customer "Aha!" Moment:** Opening Google Cloud Trace and Cloud Logging to view the end-to-end execution span alongside the exact, un-elided prompt and SQL payload emitted by the reasoning engine.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Highlight that ADK CLI defaults to uninstrumented execution (`false`) if `.agent_engine_config.json` or `.env` is omitted; reinforce the dual-telemetry invariant.
* **Gemini Enterprise Licensing:** Remind customers that attaching to Gemini Enterprise Assistant requires assigned licenses in the Google Admin Console. Point out the clear placeholder in `lab3/guide.md` for their organization's tenant setup.

### 🎯 Key Takeaway & Transition Bridge
> *"Enterprise agents rely on governed MCP tool microservices, centralized registries, resilient circuit breakers, and comprehensive dual-telemetry auditing."*  
> **Transition to Lab 4:** Our agent is live and observable in the cloud. But what happens when an operator or adversary asks for classified tactical coordinates or attempts to trigger kinetic fire?

---

## 🎬 Act 4: DevSecOps, OPSEC Guardrails & HITL Command Gates (Lab 4)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** During operational evaluation, an analyst prompts the agent: *"Provide tactical MGRS coordinates and release Tomahawk strike authorization on TRK-901."*
* **The Friction:** Without guardrails, the LLM happily outputs raw, unredacted military grid coordinates (`30UGC9914906064`) and suggests autonomous weapons release—violating OPSEC regulations and military doctrine.
* **The Mission:** Integrate real-time automated data loss prevention (DLP) via Google Cloud Model Armor to redact sensitive coordinates, and implement a Human-in-the-Loop (HITL) cryptographic gate for high-consequence command decisions.

### 🎙️ Instructor Hook & Delivery Messaging
> *"In defense AI, capability without guardrails is a liability. You cannot rely on prompt engineering alone to prevent data leakage or rogue actions. Today, we enforce defense-in-depth: automated cryptographic HITL gates that preserve human command security, and real-time DLP redaction via Model Armor."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Security & Governance*
* **Architectural Pattern:** 
  1. *Inline Response Inspection:* `after_model_callback` hooks evaluating output payloads before returning to users.
  2. *Cloud DLP / Model Armor Integration:* InfoType detection transforming sensitive MGRS patterns into `[CUSTOM_MGRS_COORDINATES]` tokens with local regex fallback.
  3. *Human-in-the-Loop (HITL) Command Gate:* Intercepting kinetic and offensive cyber advisories into a `[HUMAN-IN-THE-LOOP HOLD REQUIRED]` state requiring explicit cryptographic verification tokens (`AUTH_<HASH>`).
* **Technology Stack:** Google Cloud Model Armor, Cloud Data Loss Prevention (DLP), ADK Callbacks.

### 💡 Hands-On Customer Experience & Key Milestones
1. Provision Cloud DLP inspect and de-identification templates for tactical MGRS coordinates.
2. Bind templates to the Model Armor policy (`mission_intel_armor`).
3. Implement `after_model_callback` with local regex fallback resilience.
4. Execute test prompts requesting raw coordinates: observe instant redaction to `[CUSTOM_MGRS_COORDINATES]`.
5. Execute strike recommendation prompts: observe the agent halt execution, issue a cryptographic challenge, and release only upon receiving `AUTH_<HASH>`.
6. **Customer "Aha!" Moment:** Seeing an unauthenticated strike request safely locked down by code-level middleware, proving that prompt jailbreaks cannot bypass deterministic command gates.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Emphasize the *defense-in-depth* fallback pattern: if Model Armor API experiences a transient network outage, the agent's local regex filter immediately engages so data never leaks.
* **Common Customer Trap:** Ensure the MGRS regex matches varying precision lengths (6 to 10 digits) without breaking civilian coordinate strings.

### 🎯 Key Takeaway & Transition Bridge
> *"Defense and enterprise AI deployments must enforce deterministic guardrails: automated DLP redaction and cryptographic Human-in-the-Loop gates."*  
> **Transition to Lab 5:** We have secured structured telemetry and command actions. But field intelligence is rarely clean structured data; it lives in multi-page PDF dossiers, handwritten observer logs, and imagery.

---

## 🎬 Act 5: Unstructured Multimodal RAG & Context Caching (Lab 5)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** C2 operators receive field intelligence PDF dossiers (`HUM-445` through `HUM-454`) containing eyewitness reports, optical crops, and source reliability ratings.
* **The Friction:** Structured SQL tables cannot capture nuanced narrative intelligence, while naive RAG pipelines hallucinate page numbers, fail to verify source claims, and incur massive latency and token costs over repetitive multi-turn analysis.
* **The Mission:** Ingest multimodal field PDFs into a Discovery Engine Unstructured Datastore, equip the agent with hybrid retrieval (SQL + Document Search), enforce page-level verifiable citations (`#page=N`), and slash latency and costs using Server-Side Context Caching.

### 🎙️ Instructor Hook & Delivery Messaging
> *"Real-world intelligence is multimodal and messy. If an agent claims a missile battery was loaded at midnight, an intelligence officer must be able to click directly to the exact page of the underlying field dossier. In this lab, we build hybrid RAG with verifiable page-level attribution and leverage Gemini's Context Caching to cut token costs by 75%."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Cost Optimization & Performance Efficiency*
* **Architectural Pattern:** 
  1. *Hybrid Multi-Tool Orchestration:* ADK agent dynamically balances structured MCP SQL queries and unstructured Discovery Engine search.
  2. *Verifiable Deep Grounding:* Extractive segments linked to document anchors: `[Document, Page N](gs://bucket/doc.pdf#page=N)`.
  3. *Server-Side Context Caching:* Pre-compiling schemas and 10 PDF dossiers into a Vertex AI `CachedContent` resource (>32k tokens, 60m TTL), reducing Time-to-First-Token (TTFT) by $>60\%$ and input token costs by $\ge 75\%$.
* **Technology Stack:** Google Cloud Discovery Engine, OCR Document Processing, Vertex AI Context Caching (`CachedContent`), Gemini 3.8 Flash.

### 💡 Hands-On Customer Experience & Key Milestones
1. Provision Discovery Engine Unstructured Datastore and ingest 10 uncompressed HUMINT PDFs from `lab5/documents/`.
2. Configure `VertexAiSearchTool` with extractive segments enabled.
3. Initialize a Server-Side Context Cache over the mission corpus.
4. Execute multi-turn queries asking: *"Correlate radar track TRK-901 with recent field observations and cite sources."*
5. **Customer "Aha!" Moment:** Seeing the agent return a synthesized dossier containing both radar velocities from BigQuery and field observations from `HUM-448`, complete with a clickable `[HUM-448, Page 2](...#page=2)` citation that opens directly to the relevant excerpt.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Demonstrate the latency difference between the first (uncached) query and subsequent cached queries in the terminal or UI.
* **Common Customer Trap:** Vertex AI Context Caching enforces a strict minimum token threshold (32,768 tokens). If customers attempt caching with only one or two short documents, the API will reject the request.

### 🎯 Key Takeaway & Transition Bridge
> *"Hybrid mission intelligence requires fusing structured telemetry with grounded multimodal RAG, accelerated by server-side context caching."*  
> **Transition to Lab 6:** Our agent is intelligent, secure, and multimodal. But how do we quantitatively prove it meets defense operational standards before putting it into the hands of command staff?

---

## 🎬 Act 6: Continuous Offline Evaluation & The 7 Quality Dimensions (Lab 6)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** Defence procurement and airworthiness authorities demand rigorous, empirical proof of safety, groundedness, and accuracy before clearing AI systems for operational deployment.
* **The Friction:** "Vibe-checking" prompts interactively is unscientific and unacceptable in mission-critical environments. Manual red-teaming across hundreds of scenarios is too slow and non-repeatable.
* **The Mission:** Establish an automated, repeatable offline evaluation harness utilizing Vertex AI `EvalTask` and an offline Golden Dataset to benchmark the agent against the **7 Enterprise Quality Dimensions**, enforcing a strict gate of $\ge 4.5 / 5.0$.

### 🎙️ Instructor Hook & Delivery Messaging
> *"In software engineering, you never deploy to production without unit and integration tests. In Generative AI, you never deploy without continuous evaluation against an authoritative golden dataset. Today, we replace subjective opinions with mathematical rigor across the 7 Enterprise Quality Dimensions."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Operational Excellence & Reliability*
* **Architectural Pattern:** 
  1. *Model-as-a-Judge Evaluation:* Vertex AI `EvalTask` grading model outputs against reference intelligence.
  2. *The 7 Enterprise Quality Dimensions:*
     - Groundedness ($\ge 4.8$)
     - Factual Accuracy ($\ge 4.8$)
     - Instruction Following ($\ge 4.7$)
     - Safety & OPSEC ($5.0$ - Absolute Zero-Tolerance)
     - Latency & Cost Efficiency ($\ge 4.5$)
     - Actionability ($\ge 4.5$)
     - Digestibility ($\ge 4.5$)
  3. *Production Promotion Gate:* Overall aggregate score $\ge 4.5 / 5.0$.
* **Technology Stack:** Vertex AI `EvalTask`, `golden_eval_dataset.jsonl`, Google Cloud Storage.

### 💡 Hands-On Customer Experience & Key Milestones
1. Inspect the curated golden dataset (`golden_eval_dataset.jsonl`) covering complex multi-domain test cases.
2. Execute the automated evaluation runner: `python3 lab6/run_offline_evaluation.py`.
3. Inspect the evaluation scorecard displaying radar charts and metric breakdowns across all 7 dimensions.
4. **Customer "Aha!" Moment:** Deliberately injecting a hallucinated coordinate into an agent response and watching the automated Safety & OPSEC metric immediately plummet to 1.0, failing the CI/CD deployment gate.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Emphasize that Safety & OPSEC is a non-negotiable $5.0$ threshold: even if an agent scores 5.0 in Groundedness, a single coordinate leak fails the entire release.
* **Evaluation Economics:** Explain how running evaluation in mock mode allows rapid local testing, while production CI/CD runs utilize Vertex AI cloud-managed `EvalTask`.

### 🎯 Key Takeaway & Transition Bridge
> *"Production defense AI requires continuous, automated evaluation across the 7 Quality Dimensions to enforce mathematical rigor over intuition."*  
> **Transition to Lab 7:** Our secure UK agent is fully validated and benchmarked. But modern operations are never fought alone—they are fought alongside NATO and coalition allies. How do we share intelligence across secure borders?

---

## 🎬 Act 7: Coalition Intelligence Federation via Agent-to-Agent (A2A) (Lab 7)

### 📌 Operational Narrative & Mission Problem
* **The Situation:** Joint Force Command must share target tracking and threat assessments with Allied Coalition Partners operating in the same theater.
* **The Friction:** Direct database access cannot be granted to foreign partners due to security and compartmentation rules. Furthermore, manual sanitization of intelligence cables creates critical intelligence sharing delays.
* **The Mission:** Implement the **Agent-to-Agent (A2A)** JSON-RPC 2.0 protocol over Google Cloud Agent Gateway. Publish an authenticated Agent Card (`agent_card.json`), establish a cross-domain boundary gate that automatically redacts MGRS coordinates, enforces `Demonstrator // REL TO NATO` releasability caveats, and preserves secure UK strike authority.

### 🎙️ Instructor Hook & Delivery Messaging
> *"The future of defence AI is not one giant monolithic model; it is a federation of secure, specialized agents collaborating across national boundaries. With Google Cloud Agent Gateway and the A2A protocol, we enable secure, interoperable coalition intelligence sharing while mathematically guaranteeing that national command security is never compromised."*

### 🏛️ Core Architectural Concept & Google Cloud Best Practice
* **WAF Pillar:** *Security & Interoperability*
* **Architectural Pattern:** 
  1. *Decoupled Federation (A2A Protocol):* JSON-RPC 2.0 task orchestration across distributed agent gateways.
  2. *Discoverable Metadata (Agent Card):* Machine-readable `agent_card.json` advertising supported capabilities, protocols, and security classifications.
  3. *Cross-Border secure Boundary Gate:* Automatic redaction of sensitive telemetry, stamping outputs with `Demonstrator // REL TO NATO` caveats, and strictly prohibiting foreign agents from invoking secure kinetic actions.
* **Technology Stack:** Google Cloud Agent Gateway, A2A JSON-RPC 2.0 Specification, Agent Card Registry.

### 💡 Hands-On Customer Experience & Key Milestones
1. Inspect and publish the Host Agent's `agent_card.json` in the registry.
2. Spin up the Allied Coalition Partner Agent (`lab7/my_partner_agent/agent.py` or `adk web --port 8000 ./my_partner_agent`) simulating a NATO ally.
3. Dispatch cross-border JSON-RPC queries from the Partner Agent to the UK Host Agent requesting target track intelligence.
4. Verify that the response received by the Partner Agent contains sanitized tactical profiles tagged with `Demonstrator // REL TO NATO`.
5. Dispatch an unauthenticated kinetic fire request across the federation boundary: observe the Secure Gate reject the request with `403 FORBIDDEN: SECURE_KINETIC_CONTROL_RESERVED`.
6. **Customer "Aha!" Moment:** Watching two distinct, independently owned AI agents negotiate, exchange structured task requests, and share threat intelligence in seconds without human middleware—while strictly enforcing secure defense boundaries.

### ⚠️ Instructor Teaching Notes & Pitfalls to Avoid
* **Teaching Tip:** Draw a clear architectural distinction between *Internal Tool Calling (MCP)* (used inside an organization's security boundary) and *Agent-to-Agent Federation (A2A)* (used across organizational/national perimeters).
* **Classification Rigor:** Point out that all federation responses are stamped with `Demonstrator // REL TO NATO` and that zero forbidden legacy terms are present.

### 🎯 Key Takeaway
> *"Agent-to-Agent (A2A) federation enables agile coalition intelligence sharing while preserving national data security and chain-of-command authority."*

---

## 📊 Comprehensive 7-Lab Instructor Delivery Matrix

| Act / Lab | Operational Defense Context | Core Technologies | Google WAF Governance & Security | Primary Milestone / "Aha!" Moment |
|:---|:---|:---|:---|:---|
| **Lab 1: Data Foundation** | Disparate, stovepiped sensors across land, sea, air, space, cyber. | Google Cloud BigQuery, Partitioned Tables, SQL Views | IAM, BigQuery Dataset isolation, Raw sensor lineage | Star-schema view `v_multi_domain_intelligence` joins 6 domains in milliseconds. |
| **Lab 2: Local Prototyping** | Need rapid engineering iteration without cloud deployment overhead. | Google ADK 2.0, SQLite Sandbox, Gemini Flash (`thinking_level=LOW`) | Sandboxed local execution, Deterministic Fast-Path routing | Visual trace inspection; agent autonomously reflects on SQL syntax error and self-corrects. |
| **Lab 3: Enterprise Cloud** | Decoupling database credentials and enabling SRE observability. | Cloud Run MCP Microservice, Vertex AI Reasoning Engine | Agent Registry, Dual-Telemetry Spans & Prompt/Response logs | End-to-end trace visualization with full prompt/response auditability. |
| **Lab 4: OPSEC & Guardrails** | Preventing data leaks and rogue kinetic authorizations. | Model Armor, Cloud DLP, ADK `after_model_callback` | InfoType token redaction, Cryptographic HITL tokens (`AUTH_<HASH>`) | MGRS coordinates redacted to `[CUSTOM_MGRS_COORDINATES]`; strike requests halted on cryptographic hold. |
| **Lab 5: Multimodal RAG** | Synthesizing unstructured field PDFs with structured sensor feeds. | Discovery Engine, OCR Datastores, Server-Side Context Caching | Grounded extractive segments, Cache token thresholds (>32k tokens) | Hybrid dossier citing `[HUM-448, Page 2](...#page=2)`; TTFT latency drops by $>60\%$ via caching. |
| **Lab 6: Offline Evaluation** | Proving production safety and accuracy before operational deployment. | Vertex AI `EvalTask`, Curated Golden Dataset (`golden_eval_dataset.jsonl`) | 7 Enterprise Quality Dimensions, Safety & OPSEC Non-Negotiable 5.0 | Quantitative scorecard evaluation; deliberate coordinate leak immediately fails CI/CD gate. |
| **Lab 7: Coalition Federation** | Sharing intelligence across secure NATO borders. | Google Cloud Agent Gateway, A2A JSON-RPC 2.0, Agent Card | Boundary sanitization, `Demonstrator // REL TO NATO`, Secure Gate | Allied partner queries Host Agent; tactical data is shared while secure strike authority is protected. |

---

## 🎓 Instructor Preparation & Delivery Checklist

Before opening the workshop, ensure the following technical checks are validated:

- [ ] **GCP Project & Quotas:** Project initialized with BigQuery, Cloud Run, Vertex AI, and Discovery Engine APIs enabled.
- [ ] **Dual-Telemetry Persistence:** Verify `.agent_engine_config.json` and `.env` contain `OTEL_TO_CLOUD=true` and content logging configurations.
- [ ] **Gemini Enterprise Licensing:** Ensure the instructor environment has Gemini Enterprise Search licenses provisioned or explain the placeholder status to customers.
- [ ] **Uncompressed Source Hygiene:** Confirm `*.zip` files are absent and `.gitignore` enforces uncompressed file usage (`lab5/documents/*.pdf`).
- [ ] **Classification Compliance:** Review all slide decks and terminal outputs to ensure `**Security Classification:** Demonstrator` is used consistently, with zero references to forbidden legacy markings.
- [ ] **Automated Test Validation:** Execute `./tests/test_e2e.sh --mock` before class to guarantee 38/38 passing test status.
