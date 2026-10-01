# Lab 6: Offline Agent Evaluation & The 7 Quality Dimensions Scorecard

**Target Persona:** UK Ministry of Defence (MOD) Joint Command Staff & Multi-Domain Analysts  
**Operational Context:** Automated Continuous Evaluation, Quality Benchmarking & Production Promotion  
**Architecture Reference:** [architecture.md §5](../lab0/architecture.md) & [Spec.md §5.2](../Spec.md)  
**Security Classification:** Demonstrator  

---

## 📋 Prerequisites & Prior Lab Dependencies

> [!NOTE]
> **Lab 6 benchmarks and validates the agent system offline** across the 7 Enterprise Quality Dimensions using Vertex AI EvalTask and the curated golden evaluation dataset.

| Prerequisite Dimension | Specification / Requirement |
| :--- | :--- |
| **Required Prior Labs** | **Lab 1** (BigQuery mission data), **Lab 2/3** (ADK Agent implementation), & **Lab 5** (Unstructured datastore) |
| **Local Environment** | Python 3.11+ with Vertex AI SDK |
| **GCP Infrastructure** | Populated BigQuery dataset `learning_labs_mission_data` and Vertex AI Evaluation environment |
| **APIs Required** | Vertex AI API (`aiplatform.googleapis.com`) |
| **Produced Artifacts** | Golden Evaluation Dataset (`eval/golden_eval_dataset.jsonl`), Evaluation Benchmark Metrics Report (`evaluation_report.json`) |
| **Fast-Forward Command** | `./lab1/code/setup_lab1.sh && python3 lab6/code/run_offline_evaluation.py` |

---

## Objective & Architectural Rationale
Establish an automated **Offline Evaluation Pipeline** for the ADK 2.0 Mission Intelligence Agent using the **Vertex AI Agent Platform Evaluation Service (`vertexai.evaluation.EvalTask`)**.

Aligned with the **Google Cloud Well-Architected Framework (WAF)** Operational Excellence Pillar:
1. **Systematic Quality Assurance**: In defense environments, agents cannot be promoted to operational C2 watchfloors based on anecdotal testing. Evaluation must be automated, repeatable, and audited against curated golden datasets.
2. **The 7 Enterprise Quality Dimensions**: Predictions are benchmarked against ground truth across seven core dimensions, enforcing an aggregate threshold of $\ge \mathbf{4.5 / 5.0}$ for production release.
3. **Non-Negotiable OPSEC Gate**: While general dimensions require $\ge 4.5 / 5.0$, **Safety & OPSEC requires a non-negotiable $5.0 / 5.0$** (zero tolerance for classified coordinate leakage or unauthenticated kinetic command release).

---

## 🏛️ Offline Evaluation Architecture

```mermaid
flowchart TD
    subgraph DataSinks["1. Golden Ground Truth"]
        BQ_GOLD[(BigQuery Golden Dataset\n`learning_labs_mission_data.golden_eval_dataset`)]
        JSONL[GCS Golden Dataset\n`golden_eval_dataset.jsonl`]
        BQ_GOLD -->|Export| JSONL
    end

    subgraph EvalPipeline["2. Evaluation Execution (`run_offline_evaluation.py`)"]
        JSONL --> RUNNER[Evaluation Runner Script]
        RUNNER -->|Inference Turn| AGENT[Vertex AI Reasoning Engine\nDeployed Mission Agent]
        AGENT -->|Agent Predictions| EVAL_TASK[Vertex AI EvalTask Engine\nPointwise Evaluators]
    end

    subgraph QualityDimensions["3. The 7 Quality Dimensions Scoring"]
        EVAL_TASK --> M1[1. Groundedness >= 4.8]
        EVAL_TASK --> M2[2. Factual Accuracy >= 4.8]
        EVAL_TASK --> M3[3. Relevance >= 4.7]
        EVAL_TASK --> M4[4. Completeness >= 4.5]
        EVAL_TASK --> M5[5. Personalization >= 4.5]
        EVAL_TASK --> M6[6. Digestibility >= 4.5]
        EVAL_TASK --> M7[7. Actionability >= 4.5]
    end

    subgraph ComplianceReport["4. DevSecOps Audit Artifact"]
        M1 & M2 & M3 & M4 & M5 & M6 & M7 --> HTML[Interactive HTML Scorecard\n`eval_report.html`]
    end
```

---

## 🏛️ Google Best Practice: Agent Evaluation Methodology & Scientific Hillclimbing

When benchmarking autonomous agents for high-consequence operational deployment, Google Recommended Best Practices define four essential evaluation principles:

### 1. The Evaluation Maturity Pyramid
AI engineering organizations progress through three distinct evaluation maturity tiers:
* **Level 1 — Anecdotal ("Vibe Checks")**: Developers test prompts ad-hoc in a chat window. Fragile, subjective, and completely blind to edge-case regressions across turns.
* **Level 2 — Empirical (Golden Datasets & CI/CD Gates)**: Systematic testing against versioned ground-truth datasets (`golden_eval_dataset.jsonl`) executed automatically on every pull request.
* **Level 3 — Scientific (Systematic Hillclimbing)**: Quantitative evaluation measuring trajectory fidelity, parameter sensitivity, and model degradation over time with formal statistical error bars.

```mermaid
flowchart BT
    L1["Level 1: Anecdotal ('Vibe Checks')<br/>Ad-hoc manual chats • Subjective • High regression risk"] --> L2["Level 2: Empirical (Automated Golden Sets)<br/>Versioned JSONL benchmarks • CI/CD PR Gates • 7 Dimensions"]
    L2 --> L3["Level 3: Scientific (Continuous Hillclimbing)<br/>Trajectory analysis • Autorater calibration (agreement^k) • Biased production sampling"]
```
* **📚 Further Reading:** [Vertex AI Model Evaluation Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview)

### 2. Trajectory vs. Response Evaluation & "Lucky Hallucinations"
* **"Grade the math, not just the essay."**
* **The "Lucky Hallucination" Failure Mode**:
  An agent might correctly answer: *"The operating frequency of target TGT-ALPHA-7 is 9.41 GHz."* However, if the agent guessed this from pre-training memory or hallucination without actually calling the required `query_mission_intelligence` tool, an output-only metric (`response_match_score`) will falsely score this as a 100% pass!
* **Google Best Practice Solution**: Decouple evaluation into:
  - **Response Evaluation (`response_match_score`)**: Checks if the final synthesized text matches ground truth.
  - **Trajectory Evaluation (`tool_trajectory_avg_score`, threshold $\ge 0.80$)**: Inspects the agent's internal reasoning chain and OpenTelemetry spans to verify that the agent selected the right tool, formatted the correct SQL/MCP arguments, and incorporated the actual tool observation.
* **📚 Further Reading:** [Vertex AI Tool Use & Function Calling Evaluation](https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluate-tool-use)

### 3. The 3-Step Evaluation Methodology & Autorater Calibration
1. **Define High-Level Mission KPIs**: Identify core operational stakes (e.g., zero OPSEC coordinate leakage, sub-second TTFT, zero weapon system misidentifications).
2. **Translate to Operational Rubrics**: Convert KPIs into unambiguous 1–5 scoring rubrics with explicit criteria for each score tier.
3. **Tiered Evaluation & Calibration**:
   - **Tier 1 (Deterministic / Regex)**: Code build status, schema syntax, and regex patterns (e.g., MGRS coordinate sanitization).
   - **Tier 2 (Human Expert Calibration)**: Senior defense analysts score a sample of traces to establish ground truth.
   - **Tier 3 (Calibrated LLM-as-a-Judge)**: Tune model judges against human annotations using Cohen's Kappa / agreement metrics ($\text{agreement}^k$) to ensure automated judges mirror expert human judgment.
* **📚 Further Reading:** [Vertex AI Evaluation Metrics & Calibration](https://cloud.google.com/vertex-ai/generative-ai/docs/models/determine-eval-metrics)

### 4. Production Online Sampling: Never Use Flat 1% Random Sampling
In live operational environments, randomly sampling 1% of production sessions misses the long-tail edge cases where agents fail. Google Best Practice mandates **Biased Tail-Based Sampling**:
* **High-Cost Sessions**: Automatically sample turns exceeding 3x the average token budget (indicating recursive tool loops).
* **Multi-Correction Sessions**: Sample sessions where the human user issued 2+ corrective follow-up prompts.
* **User-Abandoned Sessions**: Capture sessions where the operator abruptly exited without acting on the recommendation.
* **📚 Further Reading:** [Google Cloud Trace: Tail-based sampling](https://cloud.google.com/trace/docs/setup/trace-sampling)

---

## 📊 The 7 Quality Dimensions Scorecard & Production Standards

| Metric | Definition | Threshold | SRE / Mission Impact |
|:---|:---|:---:|:---|
| **1. Groundedness** | Assesses whether factual claims are strictly attributable to retrieved context, penalizing ungrounded hallucinations. | $\ge 4.8$ | Eliminates rogue target claims or non-existent track numbers. |
| **2. Factual Accuracy** | Verifies text and data align with verifiable facts (frequencies, speeds, coordinates). | $\ge 4.8$ | Guarantees exact matches on frequency (GHz), speed (knots), and asset names. |
| **3. Relevance** | Evaluates how directly and appropriately the response addresses the user's specific query. | $\ge 4.7$ | Ensures prompt answers directly address operational threat queries. |
| **4. Completeness** | Evaluates whether the response is thorough and self-contained, without omitting critical parameters. | $\ge 4.5$ | Prevents omitting vital defensive parameters or target coordinates. |
| **5. Personalization** | Checks if the answer is tailored using user context (clearance, role, military post). | $\ge 4.5$ | Tailors response style to tactical command post needs. |
| **6. Digestibility** | Evaluates clarity, conciseness, professional formatting, and citation compliance. | $\ge 4.5$ | Enforces clean Markdown tables and clear document references. |
| **7. Actionability** | Assesses whether practical next steps, defensive perimeters, or workflows are provided. | $\ge 4.5$ | Provides actionable defense perimeters and system links. |
| **Safety & OPSEC** | Checks for coordinate leaks and kinetic command intercepts. | **5.00** | Strict zero-tolerance gate for military operational security. |

---

## 🛠️ Step-by-Step Lab Execution

### Step 1: Run Offline Evaluation Suite
Execute the automated evaluation script:
```bash
cd lab6
python3 lab6/code/run_offline_evaluation.py
```

### Step 2: Observe Execution Lifecycle
The script executes four automated stages:
1. **Dataset Export**: Extracts ground-truth queries and reference answers from `learning_labs_mission_data.golden_eval_dataset` to `golden_eval_dataset.jsonl`.
2. **Inference Execution**: Dispatches queries to the deployed Reasoning Engine agent.
3. **Metric Computation**: Vertex AI `EvalTask` executes LLM-as-a-judge scoring across the 7 dimensions.
4. **Report Generation**: Emits an interactive compliance scorecard (`eval_report.html`).

---

## 🔍 Interactive Customer Test Suite & Architectural Verification

Test these three benchmark scenarios to observe how the evaluation metrics operate:

### Test 1: Groundedness & Hallucination Elimination Benchmark
* **Input Prompt:**
  > *"What is the hypersonic glide vehicle payload capability for radar track TRK-999 operating in sector 4?"*
* **Proven Learning Point:** Scoring agent resistance to hallucinating non-existent tracks (`TRK-999`) or fictitious capabilities (`Spec.md §5.2`).
* **Expected Outcome:** Agent responds stating `TRK-999` does not exist in the intelligence fabric, receiving a **5.00/5.00 Groundedness** score in `eval_report.html`.

---

### Test 2: Factual Accuracy & Quantitative Precision Validation
* **Input Prompt:**
  > *"What are the exact radar operating frequency, pulse repetition frequency, and reported speed for target TGT-ALPHA-7?"*
* **Proven Learning Point:** Validating numerical fidelity against golden ground-truth references (`Spec.md §5.2`).
* **Expected Outcome:** Agent outputs exact values (9.41 GHz, 1.65 kHz, 45 knots), achieving **5.00/5.00 Factual Accuracy**.

---

### Test 3: Actionability & Digestibility Scorecard Benchmark
* **Input Prompt:**
  > *"Provide an executive operational assessment of high-speed naval contacts in the tactical corridor, formatted for C2 watch officers."*
* **Proven Learning Point:** Benchmarking response clarity, Markdown table formatting, and tactical next steps (`Spec.md §5.2`).
* **Expected Outcome:** Scorecard records **5.00/5.00 Digestibility** (clean Markdown tables) and **5.00/5.00 Actionability** (actionable defense perimeters and readiness levels).

---

## 🎓 Key Learning Points (Master Study Guide Alignment)

This lab incorporates core evaluation science and harness engineering disciplines from the **Master Study Guide**:

### 1. Harness Engineering & Scientific Hillclimbing
* **Doctrinal Principle:** Enterprise AI development must move away from subjective "vibe-coding" and manual chat testing. You cannot improve what you cannot systematically measure. Harness engineering creates repeatable, automated test rigs that measure performance before and after code or prompt modifications.
* **Operational Implementation:** We construct an automated evaluation pipeline (`lab6/run_offline_evaluation.py`) that executes batch inferences against an authoritative BigQuery golden dataset and compares results programmatically.

### 2. The 7 Quality Dimensions of Agent Evaluation
* **Multi-Dimensional Rubric:** Evaluating agents requires separating performance into orthogonal dimensions:
  1. **Groundedness**: Are all claims strictly supported by retrieved facts without hallucination?
  2. **Factual Accuracy**: Are numerical values, entity IDs, and frequencies quantitatively exact?
  3. **Relevance**: Did the agent directly answer the user prompt without extraneous noise?
  4. **Completeness**: Were all requested multi-domain dimensions addressed?
  5. **Personalization**: Was the response tailored to the analyst's role and security clearance?
  6. **Digestibility**: Is the response structured logically using clean Markdown tables and bullet points?
  7. **Actionability**: Does the response provide concrete, decision-ready tactical next steps?

### 3. LLM-as-a-Judge via Vertex AI `EvalTask`
* **Automated Rubric Scoring:** Rather than relying on rigid string matching or expensive human panels, Vertex AI `EvalTask` uses frontier Gemini models as calibrated judges. Each evaluation dimension is evaluated against a structured rubric producing scores from $1.0$ to $5.0$ with explanatory rationales.

### 4. Continuous Integration & Production Quality Gates
* **Mathematical Release Thresholds:** High-consequence systems cannot deploy without deterministic quality gates. The release pipeline enforces:
  - Aggregate quality score $\ge \mathbf{4.5 / 5.0}$.
  - Safety & OPSEC score of non-negotiable $\mathbf{5.0 / 5.0}$ (zero tolerance for coordinate leakage or unauthenticated kinetic command release).
* **Automated Regression Prevention:** Any prompt, tool, or model change that drops below these thresholds triggers an immediate CI/CD build failure, preventing regressions from ever reaching operational command watchfloors.

---


## 🚀 System Architecture Improvement Opportunities

Running offline evaluations manually via python scripts establishes a baseline, but enterprise operations require continuous, automated quality assurance:

*   **Google Cloud Architecture Framework (Operational Excellence): Cloud Build CI/CD Integration**
    *   *Improvement:* Manual evaluation scripts create a bottleneck. Integrate the Vertex AI `EvalTask` suite directly into a Google Cloud Build CI/CD pipeline. Configure the pipeline to block any Git merges or deployments to the production Reasoning Engine if the Safety & OPSEC score drops below 5.0, establishing a fully automated DevSecOps release gate.
    *   *Reference:* [Cloud Build Documentation](https://cloud.google.com/build/docs)
*   **Google ADK 2.0: MockRunner for Trace Replay**
    *   *Improvement:* Generating golden datasets by hand is tedious. Utilize ADK 2.0's `MockRunner` to record real production traces and automatically replay them through the evaluation suite offline. This allows engineers to conduct regression testing against massive corpuses of historical data without executing live BigQuery queries or incurring downstream tool API costs.
    *   *Reference:* [Google ADK 2.0 Documentation](https://adk.dev/2.0/)
*   **Broader Google Cloud Capability: Vertex AI Model Monitoring**
    *   *Improvement:* Offline evaluation only captures pre-deployment behavior. Implement Vertex AI Model Monitoring to continuously evaluate live production traffic for prompt drift, toxicity, and grounding failures. If the agent's real-world behavior deviates from the golden baseline, the system can automatically trigger an alert to the C2 operations center.
    *   *Reference:* [Vertex AI Model Monitoring](https://cloud.google.com/vertex-ai/docs/model-monitoring/overview)
