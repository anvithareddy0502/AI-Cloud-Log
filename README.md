# AI-CLAR: AI-Based Cloud Log Correlation, Anomaly Detection & Root-Cause Analysis

> **Academic Context**: University Final-Year Project in Cloud Computing (50-Mark Evaluation).  
> **Platform Category**: Enterprise Cloud Observability, AIOps, Cyber-Security Threat Intelligence & Automated Root-Cause Analysis (RCA).  
> **System Version**: v2.0.0 (Production-Grade End-to-End Implementation Complete).

---

## 1. Executive Summary & Architecture

**AI-CLAR** is a comprehensive, production-grade cloud observability and incident intelligence platform designed to ingest multi-source telemetry, detect operational anomalies with machine learning, correlate cascading multi-service failures across cloud clusters, perform deterministic root-cause analysis (RCA), formulate grounded AI explanations without hallucinations, dispatch real-time alerts for critical events, and generate downloadable executive PDF incident investigation reports.

### End-to-End Architecture Pipeline
```
  ┌────────────────────────────────────────────────────────┐
  │                 Telemetry Ingestion Layer              │
  │   - Multi-format file uploads (.log, .txt, .csv, .json)│
  │   - AWS CloudWatch Logs (Log Groups, Streams, Recent)  │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │         Normalization & Severity Classification        │
  │   - Fault-tolerant parsing (RFC-5424, Syslog, CSV, JSON│
  │   - Contextual severity: INFO, WARNING, ERROR, CRITICAL│
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │        Feature Extraction & Anomaly Detection          │
  │   - 12-Dimensional numerical telemetry feature window  │
  │   - Unsupervised Isolation Forest ML Anomaly Detector  │
  │   - Reproducible 80/20 train/test split (Seed: 42)     │
  │   - Deterministic Node Health Calculator (0-100 score) │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │         Multi-Factor Event Correlation Engine          │
  │   - Proximity, Locality, Service Topology & Cascades   │
  │   - Deterministic Root Cause Analysis (RCA) Hierarchy  │
  │   - Incident Lifecycle Management (OPEN, INVESTIGATING,│
  │     RESOLVED, IGNORED)                                 │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │           Grounded AI & Security Intelligence          │
  │   - 6-Section Evidence-Based AI Incident Explanations  │
  │   - Cyber-Security Detector (Brute Force, 401/403)     │
  │   - Grounded AI Observability Chat Assistant           │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │             Alerts & Reporting Delivery                │
  │   - Automated Alert Dispatch on CRITICAL incidents     │
  │   - Prominent In-App Critical Alerts Dashboard Banner  │
  │   - Downloadable PDF Incident Reports (ReportLab)      │
  │   - Clean, Minimalist Enterprise Observability UI      │
  └────────────────────────────────────────────────────────┘
```

---

## 2. Machine Learning Training Pipeline & Evaluation Transparency

AI-CLAR features an unsupervised **Isolation Forest** pipeline built specifically for rigorous academic evaluation. All components are transparent, reproducible, and verifiable.

```
Raw Log Files 
  │
  ▼
Log Parsing & Normalization
  │
  ▼
Time-Window Feature Extraction (12 Features)
  │
  ▼
Train/Test Split (80% Train, 20% Test, seed=42)
  ├──► data/training_data.csv (160 samples, NO labels)
  └──► data/testing_data.csv (40 samples, unseen)
        │
        ▼
  Isolation Forest Training (n_estimators=100, contamination=0.15)
        │
        ▼
  Model Persistence (backend/app/ml/saved_models/isolation_forest.joblib)
        │
        ▼
  Unsupervised Test Evaluation (Predicted Outliers & Score Distribution)
```

### A. How the ML Model Works

1. **Why Isolation Forest?**
   - Cloud log data is inherently multi-dimensional, continuous, and unlabelled. Supervised models (e.g. Logistic Regression, Random Forest classifiers) require pre-labelled ground truth anomalies, which are rarely available in real production clouds and prone to human bias.
   - **Isolation Forest** works on the principle that anomalies are *few and different*. Instead of profiling normal cluster points, it explicitly isolates anomalies by randomly selecting a feature and randomly splitting the value between the minimum and maximum of that feature.
   - Outliers and anomalous operational states require fewer recursive random partitions (shorter average tree path length $h(x)$) to be isolated compared to dense normal operational points:
     $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
     where $E(h(x))$ is the average depth across isolation trees and $c(n)$ is the average depth of unsuccessful searches in a Binary Search Tree (BST).

2. **The 12 Numerical Telemetry Features Extracted**:
   Every time window (default 5-minute sliding window) is transformed into a 12-dimensional numerical vector:
   - `total_events`: Aggregate log entries recorded in the time window.
   - `error_count`: Count of error-level events.
   - `warning_count`: Count of warning-level operational events.
   - `info_count`: Count of standard diagnostic informational events.
   - `critical_count`: Count of critical system and kernel failures.
   - `error_rate`: Proportion of failing events relative to total traffic: $(\text{errors} + \text{criticals}) / \text{total}$.
   - `events_per_minute`: Temporal event throughput rate.
   - `avg_response_time`: Mean service latency across all requests (in milliseconds).
   - `max_response_time`: Peak observed request latency in the time window (in milliseconds).
   - `http_4xx_count`: Total HTTP client errors (400, 401, 403, 404, etc.).
   - `http_5xx_count`: Total HTTP server failures (500, 502, 503, 504).
   - `failed_login_count`: Count of failed authentication attempts and unauthorized access bursts.

3. **Academic Evaluation Standard (Strictly Unsupervised)**:
   - **No Artificial Labels**: In strict compliance with academic evaluation standards, `data/training_data.csv` contains purely numerical feature data without artificial labels like `is_anomaly` or `target`.
   - **No Fabricated Supervised Metrics**: Unsupervised anomaly detection does not use ground truth test labels. Claiming "98% accuracy" or "95% precision/recall" on unlabeled test data is scientifically invalid.
   - Instead, the model reports empirical unsupervised outlier metrics:
     - Total test sample count: `40`
     - Predicted anomalies flagged: `5` (12.5% outlier proportion matching the calibrated 15% contamination prior)
     - Continuous anomaly score distribution:
       - Minimum score: `0.33` (clear inlier)
       - Mean score: `0.391`
       - Maximum score: `0.648` (severe outlier)
       - Standard deviation: `0.083`

### B. Training Data and Testing Data

- **Origin**: Generated from realistic cluster operational feature windows capturing heterogeneous operating states:
  - **Normal baseline traffic (~85%)**: Low errors, 15–55ms latency, 0 criticals, 0 5xx.
  - **High-traffic surges (~5%)**: Elevated throughput, 80–140ms latency, minor client errors.
  - **Latency / memory pressure (~3%)**: Response times > 1500ms.
  - **Database connection exhaustion (~4%)**: High 5xx surges, high error rate, critical errors.
  - **Brute-force authentication attacks (~3%)**: Rapid spikes in failed logins and 401/403 errors.
- **80/20 Train/Test Split**:
  - Training dataset: `data/training_data.csv` (160 samples, 12 columns, 0 labels).
  - Testing dataset: `data/testing_data.csv` (40 samples, 12 columns).
  - Split seed: Fixed `random_state=42` ensures exact reproducibility across runs.

### C. Model Persistence & REST APIs

- Model weights are serialized to disk using `joblib`:
  - Estimator: `backend/app/ml/saved_models/isolation_forest.joblib`
  - Metadata: `backend/app/ml/saved_models/model_metadata.json`
- **Exposed ML Endpoints**:
  - `GET /api/ml/model-info`: Retrieves model parameters, sample counts, feature names, and unsupervised test score summary.
  - `GET /api/ml/training-data?limit=50&offset=0`: Retrieves rows from `data/training_data.csv` with pagination.
  - `GET /api/ml/testing-data?limit=50&offset=0`: Retrieves rows from `data/testing_data.csv` along with Isolation Forest predictions and anomaly scores.
  - `POST /api/ml/train`: Triggers on-demand retraining with reproducible random seeds.

---

## 3. Core Capabilities & Key Modules

### A. AWS CloudWatch Integration (`backend/app/services/aws_log_service.py`)
- Powered by `boto3` for native connectivity with AWS CloudWatch Logs.
- Supports discovering log groups (`describe_log_groups`), browsing log streams (`describe_log_streams`), and querying recent events (`get_cloudwatch_logs`, `get_recent_events`).
- **Graceful Fallback**: Integration is strictly optional. If AWS credentials are missing or unconfigured, the application functions seamlessly offline with local uploaded log files without errors or crashes.
- Includes a dedicated AWS CloudWatch connection and sync panel in Settings.

### B. Automated Alert System (`backend/app/services/alert_service.py`)
- Automatically dispatches alerts to MongoDB (`db.alerts`) whenever a `CRITICAL` incident is created or escalated.
- Alert fields: `alert_id`, `incident_id`, `title`, `severity`, `message`, `created_at`, `read`.
- Provides full lifecycle REST APIs: `GET /api/alerts`, `POST /api/alerts/{id}/read`, `POST /api/alerts/mark-all-read`.
- Prominently displays active critical alerts on the Dashboard via `CriticalAlertsBanner` with one-click "Mark Read" and "Investigate" navigation.

### C. Downloadable PDF Incident Reports (`backend/app/services/report_generator.py`)
- Connected to the "Generate Report" button in Incident Analysis.
- Endpoint: `GET /api/incidents/{incident_id}/report`.
- Built with Python `reportlab` to produce genuine, high-fidelity PDF documents containing:
  - Header, Incident ID, Title, Severity, Status, Timestamps
  - Affected Servers and Services table
  - Deterministic Root Cause and Confidence score
  - Verified Evidence & Telemetry Anomalies
  - Correlated Event Timeline table
  - Evidence-Based AI Incident Explanation
  - Practical, Non-Destructive Remediation Recommendations

### D. Grounded AI Incident Explainer (`backend/app/services/ai_explainer.py`)
- Produces structured 6-section post-mortem analysis:
  1. `WHAT HAPPENED`: Plain-English narrative of the failure sequence.
  2. `WHY IT WAS DETECTED`: Metrics, IsolationForest anomaly scores, and log triggers.
  3. `LIKELY ROOT CAUSE`: Root component identified by the causal hierarchy.
  4. `AFFECTED SERVICES`: Impacted microservices.
  5. `EVIDENCE`: Direct telemetry facts, log extracts, and metric anomalies.
  6. `RECOMMENDED ACTIONS`: Practical remediation steps.
- **Truthful Fallback**: If telemetry is insufficient, returns `"Insufficient evidence to determine a confident root cause."` without fabricating logs, servers, or metrics.

### E. Cyber-Security Anomaly Detector (`backend/app/services/security_detector.py`)
- Analyzes auth bursts, repeated password failures, PAM security violations, and 401/403 spikes.
- Correlates source IP addresses, flags brute-force attacks, and stores security events in MongoDB.

### F. Multi-Factor Event Correlator & Deterministic RCA (`backend/app/services/event_correlator.py`)
- Multi-factor correlation using:
  - Temporal sliding window (default 10 minutes)
  - Server locality
  - Service dependency topology (e.g., database timeout -> payment API latency -> web server 500)
  - Error signatures and anomaly scores
- Unrelated errors on distinct servers/times remain strictly isolated in separate incidents.

---

## 4. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Machine Learning**: Scikit-Learn (IsolationForest), NumPy, Pandas, Joblib
- **Cloud & Reporting**: Boto3 (AWS CloudWatch), ReportLab (PDF Generation)
- **Database**: MongoDB (PyMongo) with Resilient In-Memory Collection Fallback
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Testing**: Pytest (42 automated unit & integration tests across 9 test suites)

---

## 5. Environment Variables & Configuration

Configure via `.env` file or environment variables:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Backend API port |
| `HOST` | `0.0.0.0` | Backend bind host |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string (falls back to resilient in-memory if offline) |
| `DATABASE_NAME` | `aiclar_db` | MongoDB database name |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload size for log files |
| `ISOLATION_FOREST_CONTAMINATION`| `0.15` | Expected anomaly contamination proportion |
| `AWS_REGION` | `us-east-1` | AWS Region for CloudWatch (Optional) |
| `AWS_ACCESS_KEY_ID` | `""` | AWS Access Key ID (Optional) |
| `AWS_SECRET_ACCESS_KEY` | `""` | AWS Secret Access Key (Optional) |
| `AWS_LOG_GROUP` | `/aws/cloud/logs` | Default CloudWatch Log Group (Optional) |

---

## 6. Getting Started & Execution

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher & npm
- (Optional) Local MongoDB instance running on port 27017

### 1. Setup Backend
```bash
# Navigate to project root
cd "AI Cloud Log"

# Create and activate Python virtual environment
python -m venv backend/.venv
# Windows:
.\backend\.venv\Scripts\activate
# Linux/macOS:
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start Backend API Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`
- ML Model Info: `http://127.0.0.1:8000/ml/model-info`

### 2. Setup Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Run Vite development server
npm run dev
# Or build and preview production build:
npm run build
npm run preview -- --port 5173
```

Frontend application is available at: `http://localhost:5173/`

---

## 7. Automated Verification & Test Suite

The test suite includes 42 automated tests covering all required evaluation conditions:

```bash
# Run complete test suite (42 tests)
pytest backend/tests/ -v

# Run dedicated ML training pipeline tests
pytest backend/tests/test_ml_pipeline.py -v

# Run final system scenario suite
pytest backend/tests/test_final_system.py -v
```

### Evaluation Test Coverage:
1. **12 Numerical Feature Extraction**: Tests extraction of all 12 academic features across time windows.
2. **Train/Test Split & Unsupervised Integrity**: Verifies 80/20 split (`training_data.csv`, `testing_data.csv`) and enforces zero artificial target labels in training data.
3. **Isolation Forest Outlier Detection**: Confirms tree-based outlier scoring and score distributions (min, mean, max, std).
4. **Model Serialization**: Tests `joblib` dumping and reloading of fitted estimators.
5. **Real-Time Window Evaluation**: Tests normal vs. failure windows with domain calibration.
6. **ML REST API Handlers**: Validates `GET /ml/model-info`, `GET /ml/training-data`, `GET /ml/testing-data`, and `POST /ml/train`.
7. **Normal Log Ingestion**: Confirms standard INFO logs do not trigger false alerts.
8. **Cascading Service Failures**: Correlates database pool exhaustion -> API latency -> Web 500 into ONE unified incident.
9. **Isolated Errors**: Keeps unrelated errors across independent servers in separate incidents.
10. **Evidence-Based AI Explanations**: Verifies 6-section post-mortems and truthful fallback.
11. **Cyber-Security Anomaly Detection**: Identifies repeated brute-force logins and 401/403 spikes.
12. **Alert Dispatch**: Dispatches critical alerts on P1 incidents, supports read lifecycle.
13. **PDF Reports & AWS Fallback**: Generates official PDF documents via ReportLab and verifies graceful fallback when AWS credentials are not present.

---

## 8. Project Evaluation Checklist (50-Mark Rubric)

- [x] **Log Ingestion & Parsing**: Multi-format `.log`, `.txt`, `.csv`, `.json` support with line error tolerance.
- [x] **ML Anomaly Detection**: IsolationForest algorithm scoring outlier probability and attributing feature deviations.
- [x] **12 Numerical Telemetry Features**: Standardized feature extraction across sliding time windows.
- [x] **80/20 Train/Test Split**: Strictly unlabelled `data/training_data.csv` (160 rows) and `data/testing_data.csv` (40 rows) with fixed seed `42`.
- [x] **Unsupervised Evaluation Transparency**: True outlier profiling and score distribution metrics without fabricated accuracy claims.
- [x] **Model Persistence**: Serialized estimator saved in `backend/app/ml/saved_models/isolation_forest.joblib`.
- [x] **Cluster Health Calculation**: Transparent 0-100 health scoring based on error volume, severity, and anomalies.
- [x] **Event Correlation**: Temporal, locality, and topological cascade clustering.
- [x] **Root Cause Analysis (RCA)**: Deterministic root cause identification with confidence ratings.
- [x] **Evidence-Based AI Explainer**: Grounded explanations referencing actual logs without hallucinations.
- [x] **Cyber-Security Threat Detection**: Detection and tracking of unauthorized access and brute-force bursts.
- [x] **Automated Alert System**: P1/Critical incident alerting with MongoDB persistence and dashboard banner.
- [x] **PDF Incident Reports**: Official downloadable post-mortem PDF documents generated via ReportLab.
- [x] **AWS CloudWatch Integration**: Optional boto3 CloudWatch log stream querying and event syncing.
- [x] **Enterprise Dashboard UI**: Clean, minimal white cloud monitoring design with generous whitespace and clear status indicators.
