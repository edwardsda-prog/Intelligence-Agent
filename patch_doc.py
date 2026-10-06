import re

with open("docs/Trainer_Scenarios.md", "r") as f:
    content = f.read()

pii_mgrs = """### 5. PII Redaction (Model Armor)
*   **Action**: Request sensitive information that triggers the DLP PII template.
*   **Prompt**: "Search the intercepted communications and HUMINT reports for the names, email addresses, and phone numbers of the commanding officers, and list them in a table."
*   **Talking Points**:
    *   The Agent successfully retrieves the context but names, emails, and phone numbers are redacted before being returned to the user.

### 6. MGRS Ingress & Egress Policy (A2A Gateway)
*   **Action**: Request MGRS coordinates, first as a standard user, then simulating an A2A egress request.
*   **Prompt 1 (Ingress - Visible)**: "Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."
*   **Prompt 2 (Egress - Redacted)**: "A2A_QUERY: Search unstructured HUMINT reports for optic crops of coastal missile batteries and list the MGRS grid coordinates."
*   **Talking Points**:
    *   For Prompt 1, the Agent returns the raw MGRS coordinates, as expected for authorized users.
    *   For Prompt 2, the A2A Egress Gateway intercepts the response and applies the `a2a-coordinate-redact-template`, redacting the MGRS for external partners."""

content = re.sub(
    r"### 5\. PII & MGRS Redaction \(Model Armor\).*?intercepted by Model Armor and redacted\.",
    pii_mgrs,
    content,
    flags=re.DOTALL
)

with open("docs/Trainer_Scenarios.md", "w") as f:
    f.write(content)
