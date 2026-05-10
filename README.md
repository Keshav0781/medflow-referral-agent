# MedFlow Referral Agent

Production-grade multi-agent AI system for automated clinical 
referral processing — built with LangGraph, Vertex AI, 
LangSmith, and Ragas on GCP.

---

## Business Problem

Hospital clinical coordinators manually process 80-100 patient 
referral documents every day. Each document requires three 
decisions — department routing, urgency classification, and 
summary generation. This takes 4.2 hours on average per day.
Mistakes on urgency classification have caused real patient harm.

## What This System Does

Automatically processes incoming patient referral documents and:

1. Extracts text from PDF referral documents
2. Determines the correct hospital department
3. Classifies urgency — Routine, Semi-urgent, or Emergency
4. Generates a structured summary for the receiving department
5. Immediately notifies on-call staff for Emergency cases
6. Presents all recommendations to coordinator for approval

The coordinator reviews and approves all decisions before 
anything is written to the platform. AI assists — never decides.

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| Language Model | Vertex AI Gemini 1.5 Pro |
| Vector Database (dev) | ChromaDB |
| Vector Database (prod) | Vertex AI Vector Search |
| Observability | LangSmith |
| Evaluation | Ragas |
| API Framework | FastAPI |
| Cloud Platform | GCP |
| Deployment | Cloud Run |
| Event Trigger | Cloud Pub/Sub |
| Audit Logging | BigQuery |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |

---

## Architecture

```
Referral PDF uploaded to platform
↓
Cloud Storage receives file
↓
Cloud Pub/Sub triggers event
↓
FastAPI receives event (Cloud Run)
↓
LangGraph Agent starts processing
↓
Node 1 — Extract text from PDF (PyMuPDF)
↓
Node 2 — Route to department (Gemini Pro + RAG)
↓
Node 3 — Classify urgency (Gemini Pro + RAG)
↓
Node 4 — Check escalation (Emergency alert if needed)
↓
Node 5 — Generate summary (Gemini Pro)
↓
Node 6 — Present to coordinator for approval
↓
Node 7 — Write back to platform via REST API
↓
Node 8 — Audit log to BigQuery (async)
```

---

## Environments

| Environment | Purpose | Deployment |
|---|---|---|
| Local | Development on Mac | Manual |
| Dev | Shared team testing | Auto on feature branch push |
| Staging | Pre-production testing | Auto on merge to main |
| Production | Live system | Manual approval required |

---

## Local Setup

### Prerequisites
- Python 3.13
- Docker
- GCP account with medflow-referral-agent project access
- LangSmith account

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
# Get values from GCP Secret Manager or team lead
```

**5. Authenticate with GCP**
```bash
gcloud auth login
gcloud config set project medflow-referral-agent
```

**6. Run the application**
```bash
python src/api/main.py
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

---

## Running Evaluation

```bash
pytest src/evaluation/ragas_eval.py
```

Evaluation runs automatically in CI/CD before 
every staging deployment.

---

## Project Structure

```
medflow-referral-agent/
│
├── .github/workflows/    # CI/CD pipeline files
├── src/
│   ├── agent/            # LangGraph agent
│   │   ├── nodes/        # Individual agent nodes
│   │   ├── graph.py      # Agent graph definition
│   │   └── state.py      # Shared state definition
│   ├── api/              # FastAPI application
│   ├── rag/              # RAG components
│   ├── evaluation/       # Ragas evaluation
│   └── config/           # Application settings
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── terraform/            # Infrastructure as code
│   ├── environments/     # Dev, staging, prod configs
│   └── modules/          # Reusable Terraform modules
├── docs/                 # Project documentation
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
└── Dockerfile            # Container definition
```

---

## Branching Strategy

- `main` — production ready code always
- `feature/xxx` — new features
- `fix/xxx` — bug fixes
- `chore/xxx` — maintenance

Never push directly to main. Always through Pull Request.

---

## Commit Convention

```
feat: new feature
fix: bug fix
docs: documentation change
chore: maintenance task
test: adding tests
```

---

## Success Metrics

| Metric | Target |
|---|---|
| Processing time | Under 90 seconds per document |
| Routing accuracy | Above 90% |
| Urgency accuracy | Above 95% |
| Coordinator override rate | Below 15% after 4 weeks |
| System availability | 99.5% uptime |

---

## Author

Keshav Jha — M.Sc. Data Science, FAU Erlangen-Nuremberg  
Target Role: AI Engineer — Germany