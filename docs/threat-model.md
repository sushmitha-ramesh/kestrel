# Threat Model

| Threat | Mitigation |
| --- | --- |
| Prompt injection in Terraform descriptions | Plan content is data, redacted and separated from system policy; it cannot change tool permissions. |
| Secret exposure | Recursive key-based redaction covers passwords, secrets, tokens, API keys, private keys, and access keys before evidence/reporting. |
| Malicious plan JSON | The parser accepts data only, avoids executing Terraform, and reports malformed input as a CLI error. |
| LLM hallucination | Findings include Terraform or AWS evidence; deterministic critical findings remain authoritative. |
| Tool misuse | Only registered read-only tools can run; unknown names and invalid arguments are rejected. |
| Excessive cost or loops | The loop has a configurable maximum step count and the mock provider is fully offline. |
| Compromised provider | No credentials or unredacted sensitive values are sent; provider output cannot invoke arbitrary commands or mutate AWS. |
| Excessive AWS permissions | The custom policy contains only explicit Describe, alarm, and caller-identity actions. |

Kestrel never runs `terraform apply`, never creates arbitrary subprocesses, and does not log credentials. Operators should use a dedicated AWS role, restrict provider egress, and treat plan files as sensitive artifacts.