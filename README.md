# incident-triage-evidence-agent

A read-only incident triage web app that classifies a synthetic incident bundle, retrieves grounded evidence, applies deterministic severity/escalation policy, and produces a concise memo.

## Why It Matters

Operational teams need fast triage support, but automated systems must remain inspectable and safe. This project demonstrates a policy-first pattern:

- Deterministic logic decides scenario, severity, and escalation
- Evidence is explicit and citation-backed
- The model (optional) only explains
- No production actions or automated remediation

## MVP Features

- Supports exactly three incident classes:
  - `certificate_issue`
  - `retry_storm`
  - `dependency_outage`
- Input via sample bundle or JSON upload
- Output includes:
  - scenario type
  - likely service
  - likely root causes
  - deterministic severity and escalation target
  - safe next actions
  - evidence citations from alerts/logs/metrics/runbooks
  - missing-context warnings
  - grounded memo (mock or OpenAI-backed)
- History persistence in SQLite via SQLAlchemy
- Server-rendered UI with Jinja2
- API routes for sample triage, upload triage, and triage lookup

## Architecture

```text
[Incident Bundle JSON]
          |
          v
[Validation / Schema Parsing]
          |
          v
[Deterministic Scenario Classifier]
          |
          v
[Deterministic Evidence Retrieval]
          |
          v
[Deterministic Policy Engine]
  (severity + escalation + actions)
          |
          v
[Memo Provider]
  - Mock provider (default)
  - OpenAI provider (optional)
          |
          v
[Persist Triage Result (SQLite)]
          |
          v
[API + Web UI]
```

## Project Layout

```text
app/
data/
tests/
notebooks/
docs/
```

## API Routes

- `POST /api/triage/sample/{sample_id}`
- `POST /api/triage/upload`
- `GET /api/triage/{triage_id}`
- `GET /health`

## Web Routes

- `GET /`
- `GET /history`
- `GET /triage/{triage_id}`
- `POST /triage/sample/{sample_id}`
- `POST /triage/upload`

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Environment Variables

See `.env.example`.

Key vars:

- `DATABASE_URL` (default local SQLite)
- `PROVIDER_MODE` (`auto`, `mock`, `openai`)
- `OPENAI_API_KEY` (optional)
- `OPENAI_MODEL` (optional)
- `MAX_UPLOAD_BYTES`

## Mock Mode (Default)

The app runs fully without `OPENAI_API_KEY`.

- If no key is present, memo generation uses `MockMemoProvider`
- Deterministic triage logic remains identical

## Optional OpenAI Mode

To enable OpenAI memo generation:

```bash
export PROVIDER_MODE=openai
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-5-mini
```

OpenAI is backend-only. The frontend never receives or uses your API key.

## Tests

```bash
pytest
```

Coverage includes:

- scenario classification
- policy severity/escalation
- evidence retrieval and citations
- mock mode behavior
- API and web route behavior

## Heroku Deployment

This repo includes:

- `Procfile`
- `runtime.txt`
- `requirements.txt`
- `.env.example`

Deploy:

```bash
heroku create incident-triage-evidence-agent
heroku config:set PROVIDER_MODE=mock
git push heroku main
```

Optional for OpenAI mode:

```bash
heroku config:set PROVIDER_MODE=openai OPENAI_API_KEY=... OPENAI_MODEL=gpt-5-mini
```

## Roadmap

- deterministic confidence decomposition by evidence type
- configurable policy thresholds in YAML
- richer retrieval over larger synthetic corpora
- export triage report (JSON/PDF)
- comparative memo outputs (mock vs model)
