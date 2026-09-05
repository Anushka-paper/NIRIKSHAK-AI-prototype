# 🚀 NIRIKSHAK AI — Local Setup Guide

> Run the full project locally in 3 steps.

## Prerequisites — Install these first
- **Python 3.11** → https://www.python.org/downloads/
- **Node.js 20+** → https://nodejs.org/en/download
- Make sure both are added to PATH during installation.

---

## Step 1 — Backend Setup (Python / FastAPI)

Open a terminal inside the unzipped folder and run:

```bash
# Create a virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install data pipeline dependencies
pip install -r data_pipeline/requirements.txt

# Start the backend server
python -m uvicorn backend.backend_api:app --reload --port 8000
```

> The backend will be live at: **http://localhost:8000**  
> You can verify it works by opening: **http://localhost:8000/docs**

---

## Step 2 — Frontend Setup (Next.js)

Open a **second terminal** (keep the first one running) inside the unzipped folder:

```bash
# Go into the frontend folder
cd frontend

# Install Node.js dependencies
npm install

# Start the frontend dev server
npm run dev
```

> The frontend will be live at: **http://localhost:3000**

---

## Step 3 — Open the App

Open your browser and go to:
```
http://localhost:3000
```

---

## Folder Structure (Quick Reference)
```
nirikshak-ai/
├── backend/          → FastAPI backend (Python)
├── frontend/         → Next.js frontend (React/TypeScript)
├── data_pipeline/    → Data ingestion & ETL scripts
├── ml_models/        → Machine learning model training
├── data/             → Raw + processed datasets & ML predictions
└── reports/          → PDF audit report generator
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Make sure `.venv` is activated before running backend |
| Port 8000 already in use | Run with `--port 8001` and update frontend `.env` |
| `npm install` fails | Make sure Node.js v20+ is installed |
| Frontend shows no data | Make sure backend is running on port 8000 first |
| `duckdb` errors | Run `pip install duckdb` inside the venv |

---

## Notes
- The `data/` folder contains all pre-processed ML predictions — **no scraping needed to run locally**.
- The ML models (`.joblib` files) are pre-trained and load automatically on startup.
- Do NOT delete `data/predictions/` — that is what powers the dashboard.
