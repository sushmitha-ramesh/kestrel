# Kestrel - Infrastructure Security AI Agent

Kestrel is an Infrastructure Security AI Agent that reviews Terraform changes before they reach AWS. It combines deterministic security checks with a bounded investigation loop that can gather additional, read-only context from Terraform and AWS.

The goal is practical: catch risky infrastructure changes early, explain what needs attention, and return a clear `APPROVE`, `REVIEW`, or `BLOCK` decision. Kestrel can investigate, but it cannot change infrastructure or bypass its safety rules.

## What Problem Does It Solve?

Terraform shows what is about to change, but a plan does not always provide enough context to understand the security and operational impact. Kestrel handles both sides of that review:

- **Known risks** are detected by deterministic rules that are explainable and testable.
- **Missing context** can be investigated by an AI agent using approved, read-only tools.

This makes Kestrel useful for local reviews and CI/CD pipelines. It is an infrastructure review assistant, not an autonomous deployment system: there is no Terraform apply path, no write-capable AWS tool, and no arbitrary shell execution.

## Start Here

Try the included examples without an AWS account, API key, or network access:

```bash
python -m pip install -e .
kestrel analyze examples/safe-plan.json --mock --no-aws
# APPROVE
kestrel analyze examples/risky-plan.json --mock --no-aws
# BLOCK
```

The risky example demonstrates findings such as public SSH access, public S3 access, and unsafe database configuration.

## Architecture

<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="820" viewBox="0 0 1440 820" role="img" aria-labelledby="architecture-title architecture-desc">
	<title id="architecture-title">Kestrel infrastructure security agent architecture</title>
	<desc id="architecture-desc">Terraform plan input flows through secret redaction and deterministic risk rules, into a bounded read-only investigation loop, and finally to an authoritative verdict and report.</desc>
	<defs>
		<linearGradient id="architecture-canvas" x1="0" y1="0" x2="1" y2="1">
			<stop offset="0" stop-color="#f7fbff"/>
			<stop offset="1" stop-color="#eef4f8"/>
		</linearGradient>
		<filter id="architecture-shadow" x="-20%" y="-20%" width="140%" height="140%">
			<feDropShadow dx="0" dy="5" stdDeviation="8" flood-color="#17324d" flood-opacity=".12"/>
		</filter>
		<marker id="architecture-arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
			<path d="M0 0 L10 5 L0 10 z" fill="#49657a"/>
		</marker>
		<style>
			.architecture-title { font: 700 30px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #102a43; }
			.architecture-subtitle { font: 400 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #526b7a; }
			.architecture-lane-title { font: 700 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; letter-spacing: 1.2px; fill: #526b7a; }
			.architecture-card-title { font: 700 16px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #102a43; }
			.architecture-card-copy { font: 400 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #526b7a; }
			.architecture-small { font: 600 11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #526b7a; }
			.architecture-tag { font: 700 11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; letter-spacing: .7px; }
			.architecture-line { stroke: #49657a; stroke-width: 2.5; fill: none; marker-end: url(#architecture-arrow); }
			.architecture-loop { stroke: #16a6a0; stroke-width: 2.5; fill: none; stroke-dasharray: 7 6; marker-end: url(#architecture-arrow); }
		</style>
	</defs>
	<rect width="1440" height="820" fill="url(#architecture-canvas)"/>
	<rect x="34" y="28" width="1372" height="764" rx="22" fill="#ffffff" stroke="#d7e3eb"/>
	<text x="72" y="78" class="architecture-title">Kestrel | Terraform security review architecture</text>
	<text x="72" y="105" class="architecture-subtitle">Deterministic controls decide the verdict. A bounded AI loop gathers optional, read-only evidence.</text>
	<rect x="1110" y="58" width="250" height="34" rx="17" fill="#e8f8ef" stroke="#a8dfc0"/>
	<circle cx="1131" cy="75" r="6" fill="#16a34a"/>
	<text x="1145" y="80" class="architecture-small" fill="#176b3a">NO APPLY | NO SHELL | READ ONLY</text>
	<rect x="60" y="140" width="288" height="550" rx="16" fill="#f5f9ff" stroke="#b8d2f4"/>
	<rect x="372" y="140" width="288" height="550" rx="16" fill="#fffbf1" stroke="#f1d18a"/>
	<rect x="684" y="140" width="420" height="550" rx="16" fill="#f2fbfa" stroke="#a8dfda"/>
	<rect x="1128" y="140" width="252" height="550" rx="16" fill="#fbf7ff" stroke="#d9b9ed"/>
	<text x="84" y="176" class="architecture-lane-title">01  INPUT</text>
	<text x="396" y="176" class="architecture-lane-title">02  LOCAL ANALYSIS</text>
	<text x="708" y="176" class="architecture-lane-title">03  BOUNDED INVESTIGATION</text>
	<text x="1152" y="176" class="architecture-lane-title">04  DECISION</text>
	<g filter="url(#architecture-shadow)">
		<rect x="88" y="214" width="232" height="112" rx="12" fill="#ffffff" stroke="#9fc3f1"/>
		<rect x="88" y="214" width="8" height="112" rx="4" fill="#2563eb"/>
		<path d="M119 245 h42 v39 h-42z M119 245 l21 17 21-17 M119 284 l15-14 M161 284 l-15-14" fill="none" stroke="#2563eb" stroke-width="3"/>
		<text x="177" y="252" class="architecture-card-title">Terraform plan</text>
		<text x="177" y="274" class="architecture-card-copy">terraform show -json</text>
		<text x="177" y="294" class="architecture-card-copy">plan.json</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="88" y="366" width="232" height="112" rx="12" fill="#ffffff" stroke="#9fc3f1"/>
		<rect x="88" y="366" width="8" height="112" rx="4" fill="#2563eb"/>
		<path d="M128 397 l18-10 18 10v20c0 13-9 23-18 27-9-4-18-14-18-27z" fill="#e8f1ff" stroke="#2563eb" stroke-width="3"/>
		<path d="M137 407 l7 7 12-14" fill="none" stroke="#2563eb" stroke-width="3"/>
		<text x="177" y="403" class="architecture-card-title">CLI entrypoint</text>
		<text x="177" y="425" class="architecture-card-copy">kestrel analyze</text>
		<text x="177" y="445" class="architecture-card-copy">loads config + plan</text>
	</g>
	<path d="M204 326 V358" class="architecture-line"/>
	<g filter="url(#architecture-shadow)">
		<rect x="400" y="214" width="232" height="112" rx="12" fill="#ffffff" stroke="#e8c46e"/>
		<rect x="400" y="214" width="8" height="112" rx="4" fill="#d97706"/>
		<path d="M440 245 h36 M440 257 h36 M440 269 h24 M440 288 h36" stroke="#d97706" stroke-width="3"/>
		<text x="490" y="252" class="architecture-card-title">Parse + redact</text>
		<text x="490" y="274" class="architecture-card-copy">normalize resource changes</text>
		<text x="490" y="294" class="architecture-card-copy">remove secret-like values</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="400" y="366" width="232" height="140" rx="12" fill="#ffffff" stroke="#e8c46e"/>
		<rect x="400" y="366" width="8" height="140" rx="4" fill="#d97706"/>
		<path d="M440 401 l13-13 13 13-13 13z M440 429 l13-13 13 13-13 13z M471 415 h23 M471 443 h23" fill="none" stroke="#d97706" stroke-width="3"/>
		<text x="508" y="405" class="architecture-card-title">Risk rules</text>
		<text x="508" y="427" class="architecture-card-copy">EC2 | S3 | IAM | RDS</text>
		<text x="508" y="449" class="architecture-card-copy">explainable findings</text>
		<rect x="508" y="464" width="94" height="22" rx="11" fill="#fff4d6"/>
		<text x="555" y="479" text-anchor="middle" class="architecture-tag" fill="#a45100">CRITICAL FIRST</text>
	</g>
	<path d="M320 422 H390" class="architecture-line"/>
	<path d="M516 326 V358" class="architecture-line"/>
	<g filter="url(#architecture-shadow)">
		<rect x="716" y="214" width="356" height="108" rx="12" fill="#ffffff" stroke="#78cfc8"/>
		<rect x="716" y="214" width="8" height="108" rx="4" fill="#0f8f89"/>
		<circle cx="759" cy="253" r="23" fill="#e8f8f5" stroke="#0f8f89" stroke-width="3"/>
		<path d="M748 253 h22 M759 242 v22" stroke="#0f8f89" stroke-width="3"/>
		<text x="799" y="251" class="architecture-card-title">AgentContext</text>
		<text x="799" y="273" class="architecture-card-copy">redacted plan + findings</text>
		<text x="799" y="293" class="architecture-card-copy">available tool definitions</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="716" y="356" width="162" height="166" rx="12" fill="#ffffff" stroke="#78cfc8"/>
		<text x="736" y="385" class="architecture-card-title">LLM providers</text>
		<rect x="736" y="402" width="116" height="24" rx="12" fill="#eef8ff"/><text x="794" y="418" text-anchor="middle" class="architecture-small">Mock</text>
		<rect x="736" y="434" width="116" height="24" rx="12" fill="#eef8ff"/><text x="794" y="450" text-anchor="middle" class="architecture-small">OpenAI / Codex</text>
		<rect x="736" y="466" width="116" height="24" rx="12" fill="#eef8ff"/><text x="794" y="482" text-anchor="middle" class="architecture-small">Anthropic / Ollama</text>
		<text x="736" y="510" class="architecture-card-copy">structured decision</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="902" y="356" width="170" height="166" rx="12" fill="#ffffff" stroke="#78cfc8"/>
		<text x="922" y="385" class="architecture-card-title">ToolRegistry</text>
		<path d="M926 415 h22 M926 431 h22 M926 447 h22" stroke="#0f8f89" stroke-width="3"/>
		<circle cx="958" cy="415" r="4" fill="#0f8f89"/><circle cx="958" cy="431" r="4" fill="#0f8f89"/><circle cx="958" cy="447" r="4" fill="#0f8f89"/>
		<text x="922" y="478" class="architecture-card-copy">read-only tools</text>
		<text x="922" y="498" class="architecture-card-copy">validated inputs</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="716" y="564" width="356" height="92" rx="12" fill="#ffffff" stroke="#78cfc8"/>
		<text x="738" y="594" class="architecture-card-title">Evidence loop</text>
		<text x="738" y="618" class="architecture-card-copy">LangGraph state: observations + round count</text>
		<text x="738" y="638" class="architecture-card-copy">finish or stop at KESTREL_MAX_AGENT_STEPS</text>
	</g>
	<path d="M632 436 H706" class="architecture-line"/>
	<path d="M894 268 H1082" class="architecture-line"/>
	<path d="M797 322 V346" class="architecture-line"/>
	<path d="M878 439 H892" class="architecture-line"/>
	<path d="M987 522 V554" class="architecture-loop"/>
	<path d="M902 590 C856 548 822 548 798 554" class="architecture-loop"/>
	<text x="1004" y="545" class="architecture-small" fill="#0f8f89">tool calls</text>
	<g filter="url(#architecture-shadow)">
		<rect x="1152" y="214" width="204" height="112" rx="12" fill="#ffffff" stroke="#caa4e2"/>
		<text x="1174" y="247" class="architecture-card-title">AWS evidence</text>
		<rect x="1174" y="263" width="32" height="28" rx="6" fill="#fff1df" stroke="#e8790c"/>
		<rect x="1181" y="269" width="18" height="4" rx="2" fill="#e8790c"/>
		<rect x="1181" y="277" width="18" height="4" rx="2" fill="#e8790c"/>
		<path d="M1220 269 q10-8 20 0v17q-10 8-20 0z" fill="#e8f7eb" stroke="#3a9b55" stroke-width="2"/>
		<path d="M1222 270 q8 7 16 0" fill="none" stroke="#3a9b55" stroke-width="2"/>
		<circle cx="1272" cy="271" r="8" fill="#f3e8ff" stroke="#9333ea" stroke-width="2"/>
		<path d="M1259 288 q13-14 26 0" fill="#f3e8ff" stroke="#9333ea" stroke-width="2"/>
		<ellipse cx="1320" cy="268" rx="15" ry="6" fill="#e8f1ff" stroke="#3478c5" stroke-width="2"/>
		<path d="M1305 268v17c0 8 30 8 30 0v-17 M1305 276c0 8 30 8 30 0" fill="none" stroke="#3478c5" stroke-width="2"/>
		<text x="1174" y="308" class="architecture-card-copy">EC2     S3      IAM     RDS</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="1152" y="356" width="204" height="112" rx="12" fill="#ffffff" stroke="#caa4e2"/>
		<text x="1174" y="389" class="architecture-card-title">Verdict policy</text>
		<text x="1174" y="414" class="architecture-card-copy">CRITICAL  -&gt;  BLOCK</text>
		<text x="1174" y="434" class="architecture-card-copy">HIGH      -&gt;  REVIEW</text>
		<text x="1174" y="454" class="architecture-card-copy">otherwise -&gt;  APPROVE</text>
	</g>
	<g filter="url(#architecture-shadow)">
		<rect x="1152" y="506" width="204" height="112" rx="12" fill="#ffffff" stroke="#caa4e2"/>
		<text x="1174" y="539" class="architecture-card-title">Report</text>
		<path d="M1177 558 h38 v39 h-38z M1184 570 h23 M1184 580 h23 M1184 590 h15" fill="none" stroke="#9333ea" stroke-width="2.5"/>
		<text x="1230" y="574" class="architecture-card-copy">Rich console</text>
		<text x="1230" y="594" class="architecture-card-copy">or JSON for CI/CD</text>
	</g>
	<path d="M1072 268 H1142" class="architecture-line"/>
	<path d="M1260 326 V348" class="architecture-line"/>
	<path d="M1260 468 V498" class="architecture-line"/>
	<path d="M632 436 C680 436 680 590 706 590" class="architecture-loop"/>
	<text x="664" y="520" class="architecture-small" fill="#0f8f89" transform="rotate(90 664 520)">read-only evidence</text>
	<line x1="84" y1="732" x2="1356" y2="732" stroke="#d7e3eb"/>
	<circle cx="96" cy="760" r="6" fill="#2563eb"/><text x="110" y="765" class="architecture-small">user input</text>
	<circle cx="210" cy="760" r="6" fill="#d97706"/><text x="224" y="765" class="architecture-small">deterministic control</text>
	<circle cx="389" cy="760" r="6" fill="#0f8f89"/><text x="403" y="765" class="architecture-small">bounded agent</text>
	<circle cx="515" cy="760" r="6" fill="#9333ea"/><text x="529" y="765" class="architecture-small">decision + reporting</text>
	<text x="1356" y="765" text-anchor="end" class="architecture-small">Kestrel v0.1.0</text>
</svg>

The infographic follows the implemented `kestrel analyze` workflow. The CLI loads and redacts a Terraform plan, deterministic rules calculate the verdict, and the bounded LangGraph agent optionally gathers evidence through validated read-only tools. Agent observations are added to the console or JSON report; they do not downgrade the deterministic verdict. `KESTREL_MAX_AGENT_STEPS` limits the investigation loop.

### How the Pieces Fit Together

| Component | Location | Responsibility |
|---|---|---|
| Terraform parsing | `terraform/` | Read plan JSON and normalize resource changes |
| Secret redaction | `terraform/evidence.py` | Remove sensitive values before they travel further |
| Risk checks | `risk/rules.py` | Apply explainable rules and create findings |
| Agent loop | `agent/planner.py` | Run the bounded LangGraph investigation cycle |
| Tool registry | `tools/` | Register tools and validate inputs and outputs |
| AWS evidence | `aws/` | Call supported read-only boto3 APIs |
| Model providers | `llm/` | Connect supported providers to one decision contract |
| Reporting | `reporting/` | Render terminal and JSON results |

## What Kestrel Checks

The V1 deterministic engine includes checks for:

- Public SSH and RDP ingress, public database ports, and unrestricted ports
- EC2 public IP assignment, IMDSv1, and disabled monitoring
- S3 public access, public ACLs, missing versioning, and destructive lifecycle settings
- RDS public accessibility, missing encryption, no backups, and missing final snapshots
- IAM wildcard actions and resources
- Encryption removal, root-volume deletion, and destructive resource changes

Findings include a rule ID, severity, confidence percentage, affected resource, explanation, and remediation guidance.

| Finding state | Verdict |
|---|---|
| One or more `CRITICAL` findings | `BLOCK` |
| No critical findings, but one or more `HIGH` findings | `REVIEW` |
| No blocking findings | `APPROVE` |

## Installation and Usage

### Prerequisites

- Python 3.10 or newer
- Terraform only when generating a plan from Terraform configuration
- An LLM API key or Ollama only when using a real model
- AWS credentials only when live AWS evidence is needed

### Install

```bash
git clone https://github.com/sushmitha-ramesh/kestrel.git
cd kestrel
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Review a Real Terraform Plan

Run this from the Terraform project you want to review:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
kestrel analyze plan.json --mock --no-aws
```

Kestrel's offline mode applies to reviewing an existing plan. Generating a new Terraform plan may still need internet or AWS access when providers or modules must be downloaded, data sources read AWS, credentials are validated, remote state is accessed, or infrastructure is refreshed. A previously generated plan can be exported and reviewed offline:

```bash
terraform show -json saved-plan.tfplan > plan.json
kestrel analyze plan.json --mock --no-aws
```

### Choose an LLM Provider

Set one provider before running `kestrel analyze`:

```bash
# Anthropic Messages API
export KESTREL_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-api-key
export ANTHROPIC_MODEL=claude-3-5-haiku-latest

# OpenAI Chat Completions
export KESTREL_LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4o-mini

# Codex-compatible OpenAI Responses API
export KESTREL_LLM_PROVIDER=codex
export CODEX_API_KEY=your-api-key
export CODEX_MODEL=gpt-5-codex

# Local Ollama
export KESTREL_LLM_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5:7b
```

Then run:

```bash
kestrel analyze plan.json --no-aws
```

The `mock` provider is the easiest way to test without a network or API key.

### Add Read-Only AWS Evidence

AWS access is optional. Configure a profile and region using the policy in [iam/kestrel-readonly-policy.json](iam/kestrel-readonly-policy.json):

```bash
export AWS_PROFILE=kestrel-read-only
export AWS_REGION=us-east-1
kestrel analyze plan.json
```

Kestrel uses supported read-only inspection calls only. It cannot apply Terraform, modify AWS resources, or execute arbitrary commands.

### Use JSON in CI/CD

```bash
kestrel analyze plan.json --mock --no-aws --json > verdict.json
```

The report includes the verdict, findings, confidence, remediation guidance, agent steps, and execution metadata.

## Provider Support

| Provider value | API | Required configuration |
|---|---|---|
| `mock` | Offline test provider | None |
| `openai` | OpenAI Chat Completions | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `codex` | OpenAI Responses API | `CODEX_API_KEY`, `CODEX_MODEL` |
| `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |
| `ollama` | Ollama local chat API | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |

All providers map their responses to the same structured Kestrel decision format. Endpoint and model capabilities still vary by provider, so test a representative plan before using a provider in CI.

## Limitations and Scope

Kestrel is a focused V1 review agent, not a complete AWS security platform:

- Coverage is strongest for Terraform changes and supported EC2, S3, IAM, and RDS inspection paths.
- It does not yet provide comprehensive Security Hub coverage, IAM MFA analysis, stale credential detection, trust-policy analysis, public snapshot checks, or full network topology discovery.
- Live AWS evidence depends on correct credentials, permissions, region, and resource identifiers.
- LLM providers can be unavailable, return malformed output, or provide incomplete recommendations. Deterministic critical findings remain authoritative.
- Kestrel does not replace Terraform validation, policy-as-code tooling, penetration testing, cloud monitoring, or human review for high-impact changes.

These limitations are deliberate: V1 prioritizes bounded behavior, explainability, and safety over pretending to provide complete cloud governance coverage.

## Project Structure

```text
src/kestrel/
├── agent/       LangGraph orchestration, state, and prompts
├── aws/         Read-only boto3 clients and typed AWS models
├── llm/         OpenAI, Codex, Anthropic, Ollama, and mock providers
├── reporting/   Rich console and JSON report renderers
├── risk/        Deterministic rules and findings
├── terraform/   Plan parsing and secret-safe evidence extraction
├── tools/       Typed tool contracts, registry, and AWS tools
├── config.py    Environment and runtime configuration
└── cli.py       Typer command-line interface
```

Most contributors will start in `cli.py`, `risk/rules.py`, `agent/planner.py`, `tools/registry.py`, `aws/client.py`, and `tests/`.

## Development and Testing

```bash
pytest
ruff check .
mypy src
```

The tests cover Terraform parsing, secret redaction, deterministic rules, allowlisted ingress, typed AWS clients and tools, provider behavior, LangGraph orchestration, and end-to-end safe/risky plan analysis.

See [docs/architecture.md](docs/architecture.md), [docs/agent-loop.md](docs/agent-loop.md), [docs/threat-model.md](docs/threat-model.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

Potential follow-on work includes public AMI and snapshot detection, deeper S3 and RDS posture checks, IAM trust-policy analysis, subnet and route-table topology, drift detection, cost impact analysis, and GitHub pull-request integration.

## License

Kestrel is released under the Apache License 2.0. See [LICENSE](LICENSE).
