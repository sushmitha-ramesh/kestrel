# Architecture

Kestrel separates five stages. `terraform.parser` loads `terraform show -json` output into immutable resource-change models and redacts secret-like keys at the boundary. `risk.rules` evaluates those models locally and produces explainable findings before any model call. `agent.planner` runs the bounded observe-decide-execute cycle. `aws.client` wraps boto3 sessions configured with profile and region, while AWS tools catch unavailable credentials without leaking details. `reporting` renders the common report as Rich terminal text or JSON.

The registry is the capability boundary: only registered, read-only tools can run. There is no apply path, shell-command tool, or arbitrary AWS API discovery. Provider adapters implement a structured decision contract and may request another allowed tool or finish.

The final policy maps critical findings to `BLOCK`, high findings to `REVIEW`, and otherwise to `APPROVE`. Agent evidence can add context but cannot downgrade deterministic critical findings.