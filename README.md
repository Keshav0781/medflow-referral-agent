# MedFlow Referral Agent

Production-grade multi-agent AI system for automated clinical referral processing — built with LangGraph, Gemini, ChromaDB, and Ragas on GCP.

**Live Demo (no login required):**

| Environment | URL |
|---|---|
| Dev | https://medflow-referral-agent-dev-togzrymjsq-ey.a.run.app |
| Staging | https://medflow-referral-agent-staging-togzrymjsq-ey.a.run.app |
| Production | https://medflow-referral-agent-prod-togzrymjsq-ey.a.run.app |

Open any URL, upload a referral PDF, and the system will automatically route it to the correct department, classify urgency, and generate a clinical summary. The coordinator can then Approve, Edit, or Reject the AI recommendation directly from the dashboard.

---

## Business Problem

Hospital clinical coordinators manually process 80–100 patient referral documents every day. Each document requires three decisions — department routing, urgency classification, and summary generation. This takes 4.2 hours on average per day. Mistakes on urgency classification have caused real patient harm.

## What This System Does

Automatically processes incoming patient referral PDFs and:

1. Extracts text from the PDF
2. Determines the correct hospital department using RAG
3. Classifies urgency — Routine, Semi-urgent, or Emergency — using RAG
4. Generates a structured clinical summary for the receiving department
5. Immediately escalates Emergency cases
6. Presents all recommendations to the coordinator for review

The coordinator reviews every decision before any action is taken. AI assists — never decides.

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Orchestration | LangGraph 1.1.10 |
| Language Model | gemini-2.5-flash (google-genai SDK) |
| Vector Database | ChromaDB 1.5.9 (pre-baked into Docker image) |
| Evaluation | Ragas |
| API Framework | FastAPI 0.136 |
| PDF Extraction | PyMuPDF |
| Cloud Platform | GCP |
| Deployment | Cloud Run |
| Event Trigger | Cloud Pub/Sub |
| Audit Logging | BigQuery |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |

---

## Architecture

```
Referral PDF uploaded via dashboard or GCS bucket
↓
Cloud Storage receives file
↓
Cloud Pub/Sub triggers event
↓
FastAPI webhook receives event (Cloud Run)
↓
LangGraph pipeline starts — 5 nodes:
↓
Node 1 — Extract text from PDF (PyMuPDF, no LLM)
↓
Node 2 — Route to department (ChromaDB RAG + gemini-2.5-flash)
↓
Node 3 — Classify urgency (ChromaDB RAG + gemini-2.5-flash)
↓
Node 4 — Check escalation (Emergency alert, no LLM)
↓
Node 5 — Generate clinical summary (gemini-2.5-flash)
↓
Results presented to coordinator on dashboard
↓
Coordinator clicks Approve / Edit / Reject
↓
Action logged to BigQuery (full audit trail)
```

Processing time: ~40–48 seconds per document (target: under 90 seconds).

---

## Coordinator Dashboard

The dashboard at the root URL (`/`) gives the coordinator full control:

- **Stats cards** — total processed, emergency, semi-urgent, routine counts
- **Referral cards** — urgency colour coded, confidence score bars, AI summary
- **Approve** — accepts AI recommendation, removes from pending list, logs to BigQuery
- **Edit** — opens modal, coordinator changes department and/or urgency, confirms, logs edited values to BigQuery
- **Reject** — rejects referral, removes from pending list, logs to BigQuery
- **Drag and drop upload** — coordinator can upload PDFs directly from the dashboard
- **Auto-refresh** — every 30 seconds

---

## Environments

| Environment | Purpose | Deployment |
|---|---|---|
| Dev | Testing after every merge | Auto on merge to main |
| Staging | Pre-production gate | Auto after dev — requires Ragas accuracy gate to pass |
| Production | Live system | Manual trigger + manual approval in GitHub Actions |

All three environments use isolated GCP resources — separate BigQuery datasets, Cloud Storage buckets, and Pub/Sub topics.

---

## Local Setup

### Prerequisites
- Python 3.11 or 3.13
- Docker
- GCP account with `medflow-referral-agent` project access

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/Keshav0781/medflow-referral-agent.git
cd medflow-referral-agent
```

**2. Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
# Edit .env and fill in your real values
```

**5. Authenticate with GCP**
```bash
gcloud auth login
gcloud config set project medflow-referral-agent
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform"
```

**6. Run RAG ingestion — populates ChromaDB locally**
```bash
python -m src.rag.ingestion
```

**7. Run the application**
```bash
python -m src.api.main
```

**8. Verify health endpoint**
```bash
curl http://localhost:8080/health
```

---

## Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/
```

43 tests total — unit and integration. BigQuery is mocked in integration tests.

---

## Evaluation

```bash
pytest src/evaluation/ragas_eval.py
```

Runs automatically in CI/CD before every staging deployment. Blocks deployment if accuracy is below threshold.

| Metric | Threshold |
|---|---|
| Routing accuracy | 90% |
| Urgency accuracy | 95% |

---

## Project Structure

```
medflow-referral-agent/
├── .github/workflows/
│   ├── ci.yml                 # Runs 43 tests on every push
│   ├── deploy-dev.yml         # Auto deploy on merge to main
│   ├── deploy-staging.yml     # Ragas gate then deploy
│   └── deploy-prod.yml        # Manual trigger + manual approval
├── src/
│   ├── agent/
│   │   ├── nodes/             # 5 agent nodes
│   │   ├── graph.py           # LangGraph graph definition
│   │   └── state.py           # ReferralState TypedDict
│   ├── api/main.py            # FastAPI app — webhook, coordinator actions, dashboard
│   ├── config/settings.py     # Pydantic v2 settings
│   ├── dashboard/index.html   # Coordinator dashboard UI
│   ├── evaluation/            # Ragas evaluation pipeline
│   └── rag/ingestion.py       # ChromaDB ingestion — runs during Docker build
├── tests/
│   ├── unit/                  # 26 unit tests
│   └── integration/           # 17 integration tests
├── terraform/
│   ├── environments/          # Dev, staging, prod configs
│   └── modules/               # Cloud Run, Pub/Sub, BigQuery, Storage
├── startup.sh                 # Starts uvicorn
├── Dockerfile                 # Multi-stage, ChromaDB pre-baked
├── docker-compose.yml         # Local dev
├── requirements.txt
└── .env.example
```

---

## Git Workflow

Never push directly to main. Always:

```
feature branch → PR → CI passes → merge → delete remote branch → git pull origin main → git branch -d local
```

Production deployments: GitHub Actions → Deploy Production → Run workflow → enter verified staging image SHA → approve gate.

---

## Commit Convention

```
feat:  new feature
fix:   bug fix
docs:  documentation change
chore: maintenance task
test:  adding tests
```

---

## Success Metrics

| Metric | Target |
|---|---|
| Processing time | Under 90 seconds per document |
| Routing accuracy threshold | 90% |
| Urgency accuracy threshold | 95% |
| System availability | 99.5% uptime |

---

## Author

Keshav Jha — M.Sc. Data Science, FAU Erlangen-Nuremberg  
ex-Accenture Senior Analyst | Working Student, Siemens Healthineers AI Team  
Target Role: AI Engineer — Germany  
GitHub: https://github.com/Keshav0781