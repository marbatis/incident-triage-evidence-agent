# Payments Runbook

## Retry storm response
- Check retry rate and p99 latency before changing retry policy.
- If `429` and timeout errors appear together, reduce retry concurrency and increase backoff.
- Protect partner gateway by rate-limiting noisy traffic.

## Queue recovery
- Stabilize queue depth and process backlog gradually.
- Escalate to service owner oncall if saturation persists beyond 15 minutes.
