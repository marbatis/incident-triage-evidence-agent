# Task Environment

## 1. Rational Objective

Given a synthetic incident bundle, produce a grounded triage report that is safe, inspectable, and operationally useful. The system must prioritize deterministic policy decisions and use model generation only for explanatory memo text.

## 2. PEAS

- Performance:
  - Correct scenario classification for supported incident classes
  - Deterministic severity/escalation aligned to policy
  - Explicit evidence citations and missing-context flags
  - Stable mock-mode operation with no external key
- Environment:
  - Synthetic incident bundles, local runbooks, alerts/metrics metadata, SQLite persistence
- Actuators:
  - API responses, server-rendered triage pages, persisted triage history
- Sensors:
  - Incident payload fields (alerts, metrics, logs, service topology, runbook refs, recent changes)

## 3. Environmental Dimensions

- Observability quality varies by incident payload completeness.
- Incident signals are noisy; classifier and policy are heuristic but deterministic.
- Runtime operates in stateless request cycle with local persistent store.
- Provider behavior can vary by configuration (`mock` vs `openai`) but policy output does not depend on model output.

## 4. Problem Formalization

Input: incident bundle `B` with typed fields.

Intermediate deterministic functions:

- `scenario = classify(B)`
- `service = detect_service(B)`
- `evidence = retrieve(B, scenario, service)`
- `decision = policy(B, scenario, evidence)`

Optional explanatory function:

- `memo = provider(result)`

Output: structured triage result `R` with severity, escalation, actions, citations, and missing context.

## 5. Architecture Choice

A workflow architecture is used to preserve safety and inspectability:

1. input validation
2. scenario classification
3. local evidence retrieval
4. deterministic policy scoring and escalation logic
5. optional memo drafting
6. persistence
7. API/UI rendering

This avoids hidden authority in the model and supports strict mock-mode operation.

## 6. Guardrails / Workflow Maturity

- No production actions or auto-remediation
- Deterministic policy has final authority
- Model usage is backend-only and optional
- Upload payloads are JSON-validated and size-limited
- Auditability via stored triage results and visible evidence citations
- Missing evidence is surfaced explicitly rather than guessed
