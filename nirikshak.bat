@echo off
REM Nirikshak 2.0 - Helper Scripts
REM Run this file to see all available commands

if "%1"=="scrape" (
    echo [Nirikshak] Running live MPLADS scraper...
    .venv\Scripts\python data_pipeline/live_scraper.py
    goto :eof
)

if "%1"=="train" (
    echo [Nirikshak] Training all 6 ML models...
    .venv\Scripts\python ml_models/train_all.py
    goto :eof
)

if "%1"=="backend" (
    echo [Nirikshak] Starting FastAPI backend on port 8000...
    .venv\Scripts\python -m uvicorn backend.backend_api:app --host 0.0.0.0 --port 8000 --reload
    goto :eof
)

if "%1"=="etl" (
    echo [Nirikshak] Running ETL pipeline...
    .venv\Scripts\python data_pipeline/etl_pipeline.py
    goto :eof
)

if "%1"=="full" (
    echo [Nirikshak] Running full pipeline: scrape + etl + train...
    .venv\Scripts\python data_pipeline/live_scraper.py
    .venv\Scripts\python data_pipeline/etl_pipeline.py
    .venv\Scripts\python ml_models/train_all.py
    echo [Nirikshak] Full pipeline complete!
    goto :eof
)

echo.
echo  Nirikshak 2.0 - Available Commands:
echo  =====================================
echo  nirikshak.bat scrape    - Run live MPLADS data scraper
echo  nirikshak.bat etl       - Run ETL pipeline (CSV to DuckDB)
echo  nirikshak.bat train     - Train all 6 ML models
echo  nirikshak.bat backend   - Start FastAPI backend (port 8000)
echo  nirikshak.bat full      - Run scrape + etl + train in sequence
echo.
