# Auth Runbook

## Certificate and TLS failures
- If `x509 certificate has expired` appears, verify certificate expiry immediately.
- Validate trust chain and endpoint certificate mapping.
- Perform controlled certificate rotation with rollback to previous known-good certificate.

## Escalation
- Escalate to incident commander when auth handshake failure impacts customer login.
