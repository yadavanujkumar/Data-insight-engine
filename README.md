# Decision Intelligence Platform

A production-ready, full-stack platform for data ingestion, quality analysis, forecasting, simulation, and AI-driven decision support.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Decision Intelligence Platform                 │
├─────────────┬───────────────────────────────────────────────────┤
│  Frontend   │  Next.js 14 · TypeScript · Tailwind · Recharts    │
│  (Port 3000)│  Dashboard · NLQ · Forecasting · Recommendations  │
├─────────────┼───────────────────────────────────────────────────┤
│  Backend    │  FastAPI · Python 3.11 · SQLAlchemy · Pydantic v2 │
│  (Port 8000)│  12 API modules · 11 service classes              │
├─────────────┼─────────────────┬─────────────────────────────────┤
│  PostgreSQL │  Redis          │  Prometheus + Grafana           │
│  (Port 5432)│  (Port 6379)   │  (Port 9090 / 3001)             │
└─────────────┴─────────────────┴─────────────────────────────────┘
```

## Modules

| Module | Description |
|---|---|
| **Ingestion** | CSV/Excel upload with column profiling and lineage |
| **Cleaning** | Missing value imputation, outlier clipping, deduplication |
| **Quality** | Completeness, consistency, validity, uniqueness scoring |
| **Graph** | Entity-relationship graph with neighbour traversal |
| **Analytics** | KPIs, trend analysis, anomaly detection |
| **Forecasting** | Time series forecasting with confidence intervals |
| **Simulation** | Monte Carlo simulation and what-if scenarios |
| **Recommendations** | Automated, impact-ranked data insights |
| **NLQ** | Natural language queries over your data |
| **Alerts** | Threshold-based alerting with lifecycle management |
| **Reports** | Report creation and management |
| **Metrics** | System metrics recording and aggregation |

## Modular Service Orchestration

The backend now includes a lightweight modular framework under `backend/app/core/`:

- `base_service.py`: common service execution interface
- `service_registry.py`: runtime service registration for independent orchestration
- `event_bus.py`: publish/subscribe communication between services

Optional integration adapters are available under `backend/app/integrations/`:

- `langchain_integration.py`: exposes registered services as LangChain tools when LangChain is installed
- `langgraph_integration.py`: builds a quality → recommendation workflow with LangGraph when installed

If LangChain/LangGraph are not installed, both adapters gracefully fall back to local callable wrappers.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Run with Docker Compose

```bash
git clone https://github.com/your-org/Data-insight-engine.git
cd Data-insight-engine

# Start all services
docker compose up -d

# Check services are healthy
docker compose ps
```

Services available:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### Local Development

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your database credentials

uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## API Documentation

Full interactive docs available at http://localhost:8000/docs

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/datasets/upload` | Upload CSV/Excel dataset |
| `GET` | `/api/v1/datasets` | List all datasets |
| `GET` | `/api/v1/quality/{id}` | Get quality score |
| `POST` | `/api/v1/cleaning/run` | Run data cleaning |
| `POST` | `/api/v1/analytics/run` | Run analytics |
| `POST` | `/api/v1/forecasting/run` | Run time series forecast |
| `POST` | `/api/v1/simulation/run` | Run Monte Carlo simulation |
| `POST` | `/api/v1/recommendations/generate/{id}` | Generate recommendations |
| `POST` | `/api/v1/nlq/query` | Natural language query |
| `GET` | `/api/v1/alerts` | List alerts |
| `POST` | `/api/v1/alerts` | Create alert rule |
| `GET` | `/api/v1/metrics` | System metrics summary |

### Example: Upload and Analyze

```bash
# Upload a dataset
curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@data.csv" \
  -F "name=Sales Data"

# Get quality score (replace 1 with dataset id)
curl http://localhost:8000/api/v1/quality/1

# Run forecast
curl -X POST http://localhost:8000/api/v1/forecasting/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "target_column": "revenue", "date_column": "date", "horizon": 30}'

# Natural language query
curl -X POST http://localhost:8000/api/v1/nlq/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the average revenue?", "dataset_id": 1}'
```

## Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace decision-intelligence

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=username=postgres \
  --from-literal=password=YOUR_PASSWORD \
  -n decision-intelligence

kubectl create secret generic backend-secret \
  --from-literal=database-url=postgresql://postgres:YOUR_PASSWORD@postgres:5432/decision_intelligence \
  --from-literal=secret-key=YOUR_SECRET_KEY \
  -n decision-intelligence

# Apply manifests
kubectl apply -f k8s/ -n decision-intelligence

# Check status
kubectl get pods -n decision-intelligence
```

## Environment Variables

### Backend (.env)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `SECRET_KEY` | *(required)* | JWT signing key |
| `UPLOAD_DIR` | `uploads` | File upload directory |
| `OPENAI_API_KEY` | *(optional)* | OpenAI API key for enhanced NLQ |
| `DEBUG` | `false` | Enable debug mode |

### Frontend

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

## Technology Stack

### Backend
- **FastAPI** 0.110 – High-performance async API framework
- **SQLAlchemy** 2.0 – ORM with PostgreSQL
- **Pydantic** v2 – Data validation and serialization
- **pandas / numpy / scipy** – Data processing and statistics
- **scikit-learn / xgboost** – Machine learning models
- **prometheus-client** – Metrics instrumentation

### Frontend
- **Next.js** 14 (App Router) – React framework
- **TypeScript** – Type safety
- **Tailwind CSS** – Utility-first styling
- **Recharts** – Data visualization
- **Axios** – HTTP client

### Infrastructure
- **Docker / Docker Compose** – Containerization
- **Kubernetes** – Orchestration
- **Prometheus / Grafana** – Monitoring
- **GitHub Actions** – CI/CD

## Development

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Code Style

```bash
cd backend
pip install flake8
flake8 app/ --max-line-length=100
```

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
