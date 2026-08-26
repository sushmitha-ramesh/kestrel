# Agent Loop

Kestrel qualifies as an AI agent because it performs a bounded action-observation cycle rather than asking a model for a one-shot summary:

```text
Observe plan and deterministic findings
  -> reason about missing evidence
  -> select an allowed structured tool
  -> execute it
  -> observe the result
  -> repeat or return a final decision
```

Each step records the selected tool, validated arguments, a short rationale, and the redacted observation. Private chain-of-thought is neither requested nor stored. `KESTREL_MAX_AGENT_STEPS` bounds latency and cost. The mock provider demonstrates the same protocol offline; real provider adapters can make selection dynamically.

Deterministic safeguards remain outside the LLM. A critical public management exposure or destructive security-control change remains `BLOCK` even if a provider returns an approving decision.