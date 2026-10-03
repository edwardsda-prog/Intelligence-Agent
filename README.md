# Intelligence Agent: Multi-Domain Agentic Intelligence Application

Welcome! The Intelligence Agent is a demonstrator application built for the UK Ministry of Defence (MOD). This project shows how we can use Generative AI to securely connect the dots across different intelligence sources—like radar tracks, cyber threat reports, and PDF field documents—in seconds instead of hours.

Whether you are a frontline analyst, the engineer deploying the system, or the security expert keeping it locked down, this guide will help you understand what this platform does and how it works for you.

---

## 1. The End User Experience (Intelligence Analysts)

As an intelligence analyst using **Gemini Enterprise**, your goal is to make fast, accurate decisions without getting bogged down in manual data gathering. 

*   **Ask Natural Questions:** You don't need to write complex database queries. You can ask Gemini things like, *"Cross-reference radar track TRK-901 with the intelligence in HUM-448."* The agent does the heavy lifting, simultaneously pulling live data from BigQuery and scanning unstructured PDF reports to give you a single, unified answer.
*   **Trust But Verify (Secure Citations):** Hallucinations are not an option. When the agent references a PDF field report, it provides a direct, clickable link to the exact page of the secure document. You can instantly verify the source data yourself natively within the Gemini UI.
*   **A Conversation That Remembers:** The agent features long-term memory. If you ask a follow-up question about "those targets," it remembers exactly which radar tracks and reports you were just discussing, allowing for a seamless, continuous workflow.

---

## 2. The Operations Experience (Platform & FinOps Engineers)

For the team deploying and monitoring the application, reliability and cost-control are paramount. This application is built on the **Google Agent Developer Kit (ADK 2.0)** and deployed as a managed **Vertex AI Reasoning Engine**, which takes the headache out of infrastructure management.

*   **Deploy with Ease:** Forget about managing servers or handling cold-starts. Deploying the agent is straightforward, and the Reasoning Engine automatically scales to meet demand.
*   **See Everything (Observability):** We provide out-of-the-box Google Cloud Monitoring dashboards. You can track exactly how long each tool takes to run and trace the agent's thought process step-by-step using OpenTelemetry.
*   **Control Costs (FinOps):** AI token costs can spiral if left unchecked. Our dashboards visualize your "Token Burn," allowing you to see exactly how many input and output tokens are consumed per session. This helps you prevent runaway loops and right-size your models to save money.
*   **Memory Management:** Operations also oversees the multi-tier memory system (from working memory to long-term threat domain tracking), ensuring the agent stays smart without bloating its context window and driving up costs.

---

## 3. The Security Experience (SecOps & Coalition Partners)

Security isn't an afterthought; it's the foundation of the platform. This application operates under a Zero-Trust architecture designed for military-grade compliance.

*   **Human-in-the-Loop (HITL):** AI should recommend, but humans must decide. If the agent suggests a high-consequence action (like a kinetic strike or an offensive cyber countermeasure), the system halts. It requires explicit cryptographic authorization from command staff before proceeding.
*   **Inline Data Redaction (Model Armor):** We use Google Cloud Model Armor and Data Loss Prevention (DLP) to actively scan everything the AI reads and writes. If it detects sensitive information—like raw Military Grid Reference System (MGRS) coordinates or UK National Caveats—it automatically redacts them before they ever reach the screen.
*   **Identity First (SPIFFE):** We don't use static passwords or service account keys that can be leaked. The agent uses temporal, workload-based identities to securely access databases and search engines.
*   **Safe Coalition Sharing:** Need to share intelligence with NATO partners? The Agent-to-Agent (A2A) protocol allows our agent to securely communicate with allied agents. Our security boundaries automatically sanitize the outgoing information to ensure only releasable data crosses the network.

---

## 4. Try It Out: Trainer Scenarios

If you are demonstrating this platform, we have built three specific scenarios that perfectly highlight these personas in action:

*   **Scenario 1:** Highlights the **End User** experience, focusing on multi-domain reasoning, secure citations, and memory.
*   **Scenario 2:** Highlights the **Operations** experience, showing off the Observability and FinOps dashboards.
*   **Scenario 3:** Highlights the **Security** experience, demonstrating the HITL command gates, Model Armor redaction, and NATO partner integration.

*(For detailed scripts, please see `docs/Trainer_Scenarios.md`)*
