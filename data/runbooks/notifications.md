# Notifications Runbook

## Dependency outage handling
- Confirm downstream dependency status and failure mode.
- Enable degraded mode if dependency unavailable and queue depth is increasing.
- Coordinate with dependency owner and document connection refused evidence.

## Recovery
- Throttle non-critical notifications while primary channel is unstable.
- Escalate to incident commander when dependency outage causes critical delivery failures.
