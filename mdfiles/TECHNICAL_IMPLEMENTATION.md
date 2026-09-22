# NIRIKSHAK-AI — Technical Implementation Summary

Quick-reference table for presentation slides. Grouped by system layer.

## Frontend

| Component | Technology | Details |
|---|---|---|
| Framework | Next.js (App Router) | Server + client components, server-side data fetching for the landing page |
| Language | TypeScript | Strict typing across pages, API routes, and shared types |
| Styling | Tailwind CSS | Responsive design (mobile-first breakpoints), custom design tokens |
| Charts & Visualizations | Recharts | Donut charts, bar charts, line charts — all driven by live API data |
| Geographic Visualization | Custom SVG India map | Clickable state polygons, real-time risk-based coloring |
| Auth State | React Context (`authContext.tsx`) | JWT-based session, role-aware UI gating (`useRequireAuth`) |
| Animation | Framer Motion | Animated stat counters on landing page |

## Backend Services

| Service | Framework | Port/Role | Responsibilities |
|---|---|---|---|
| Compliance API (`api.py`) | FastAPI + SQLAlchemy | 8000 | Auth, RBAC, works CRUD, alerts, findings, admin/user provisioning |
| ML/Analytics API (`backend/backend_api.py`) | FastAPI + pandas/DuckDB | 8001 | Overview stats, state aggregation, anomaly detection, ML predictions, compliance summary |
| Database | SQLite (dev) | — | Two independent instances (one per service) with matching seed data |

## Authentication & Access Control

| Feature | Implementation |
|---|---|
| Auth mechanism | JWT (PyJWT), bcrypt password hashing |
| Roles | 4 personas: MP, State Nodal Authority, District Authority, Ministry |
| Scoping | Server-side SQLAlchemy query filters on every request (not just login) — re-validated per request so deactivation takes effect immediately |
| Account provisioning | Invite-based — Ministry creates account, invitee sets own password via one-time link |
| Session handling | `useRequireAuth()` hook gates all data pages; landing page kept public |

## Machine Learning

| Model | Algorithm | Purpose |
|---|---|---|
| Delay-Risk Predictor | HistGradientBoostingClassifier (scikit-learn) | Predicts probability a work will miss its completion deadline |
| Label design | Censored/hazard-style labeling | Avoids survivorship bias from naive "completed-only" labeling |
| Explainability | SHAP (TreeExplainer) | Real per-prediction feature attribution, not heuristic scoring |
| Anomaly Detection | Isolation Forest (unsupervised) | Flags statistically anomalous works (fund utilization, billing patterns) |
| Forecasting | Prophet / trend projection | 6-month expenditure forecast per state/entity |

## LLM-Grounded Explanations

| Stage | Implementation |
|---|---|
| Grounding | Structured payload built from SHAP values + work metadata (`context.py`) |
| Generation | Forced tool-use call to Claude (Anthropic API) |
| Validation | Numeric claims in the LLM output are checked against the grounding payload before being shown |
| Fallback | Rule-based template explanation when no API key / invalid response |
| Caching | SQLite cache keyed on `(work_id, model_version)` to avoid redundant API calls |

## Compliance Engine

| Feature | Implementation |
|---|---|
| Rules engine | Custom Python rule set (jurisdiction, financial ceilings, SLA deadlines, SC/ST quotas, negative-list keywords) |
| Severity tiers | BLOCK / WARN / REVIEW — only BLOCK/CRITICAL raises alerts |
| Duplicate detection | RapidFuzz `token_set_ratio` + custom distinguishing-token gate (cuts false positives from boilerplate phrasing) |
| Violation sampling | Fair round-robin sampling across rule types so no single rule dominates a capped API response |
| Case management | Alert → Assign → Resolve workflow via `ComplianceFinding`/`ComplianceControl` models |

## Data Pipeline

| Stage | Tooling |
|---|---|
| Source | Public MPLADS dataset (mplads.gov.in), scraped via `requests`/`BeautifulSoup` |
| Storage | Canonical CSVs (per-parliament, per-feature) + DuckDB for fast aggregation |
| Feature engineering | 118 engineered features per work record |
| Scheduled retraining | GitHub Actions nightly workflow — re-scrapes, re-trains delay-risk model, commits updated artifacts |

## Deployment

| Layer | Platform |
|---|---|
| Frontend | Vercel (Next.js) |
| Compliance API | Railway (separate service, `api.py`) |
| ML/Analytics API | Railway (separate service, `backend_api.py`) |
| CI/CD | GitHub Actions (nightly model retraining), Railway auto-deploy on push |

---
*Generated for presentation use — see `mdfiles/PRD_GAP_CLOSURE.md` and `mdfiles/USER_GUIDE.md` for full detail.*
