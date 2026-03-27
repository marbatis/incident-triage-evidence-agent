# Build Notes

- Implemented deterministic triage core first: classifier, retrieval, policy engine.
- Added SQLAlchemy persistence for triage history (`triage_history` table).
- Added provider abstraction with mock default and optional OpenAI implementation.
- Added API and web routes sharing the same triage service.
- Added strict upload size validation and JSON-only upload parsing.
- Added sample corpora (3 incident bundles + runbooks) designed to exercise each scenario type.
- Added tests for core logic, routing, and mock-mode operation.
