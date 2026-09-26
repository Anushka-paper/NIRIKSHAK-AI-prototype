# NIRIKSHAK-AI — Screen Recording Flow

Maps the final demo script to exact clicks/URLs. Login once as **Ministry**
(`ministry@nirikshak.demo` / `demo1234`) — it's the only role with unrestricted,
national-scope access to every page below.

## Before you hit record

1. Start all three services and open the app once, end-to-end, so every
   backend cache is warm (see "Why this matters" below).
2. Specifically **open Compliance Audit once and let it fully load** before
   recording — the very first load after a server restart can take
   10-40+ seconds (it evaluates ~98K work records from scratch). Every
   load after that is 1-3 seconds. Do a full dry-run of the whole flow
   below once, then record the real take.
3. Log in as Ministry and keep that session for the whole recording — no
   role-switching needed since Ministry sees everything.

## Recording flow (matches script timestamps)

| Time | Script section | What to click | Notes |
|---|---|---|---|
| 0:00–0:25 | Hook — montage | Land on `/` (public, no login needed for this shot). Scroll from hero down to the **Live MPLADS Risk Intelligence** section (India map). | Do this as a fast scroll/cut — hero → stat strip → map. Then jump-cut to brief glimpses of a project's risk gauge, the AI explanation card, and the Compliance dashboard (reuse footage from later sections when editing, or quickly flash through them here). |
| 0:25–0:48 | Overview: Why NIRIKSHAK-AI | Log in → lands on `/overview`. Show the 4 KPI cards, the **Project Status Distribution** donut, then scroll to **Consolidated Financial Lifecycle & Budget Flow** bar chart. | This page has the KPI+chart combo the script calls "Overview Dashboard." The India map itself lives only on `/`, not here — if you want map + overview together in one continuous shot, film the landing page map first, then a hard cut to `/overview` right after. |
| 0:48–1:05 | States & MP Performance | Click **Explore → Browse States**. Show the Top/Bottom-10 completion bar charts, then click **View Details** on any state card. On the state page, show the KPI cards, financial chart, then scroll to the **MP Performance** section (top-10 bar chart + ranked list). | State page URL pattern: `/overview/state/<state-id>`. |
| 1:05–1:25 | Project + AI Risk Prediction | Click **Explore → Projects**, open any project (or reuse `CW_000018`, a real completed work). Click **Run ML Risk Inference**. | Wait for the risk gauge, "+N Days" projected delay, and "Administrative Action" card to render — this is a real model call, not instant; give it 3-5 seconds on camera or trim in editing. |
| 1:25–1:43 | Explainable AI (USP) | On the same project page, click **Get Full AI Explanation**. | Shows SHAP-derived "Key Risk Drivers" and a synthesized explanation card. Locally this will show a "Template fallback (LLM unavailable)" badge unless `ANTHROPIC_API_KEY` is set — the explanation text itself is still real, SHAP-grounded, and demo-ready either way. If you want the live LLM badge instead, set that env var before starting `backend_api.py`. |
| 1:43–2:00 | Anomaly & Fraud-Risk Detection | Click **Explore → Anomalies**. Default view is **Analytics Graphs** — show the 4 KPI cards, the Risk Band donut, the scatter plot, then scroll to **State-wise Anomaly Volume** and **Irregularity Root Causes**. | Click **Flagged Works** tab briefly to show the searchable table if time allows. |
| 2:00–2:15 | Compliance + Duplicate Detection | Click **Compliance Audit** in the top nav. Show the 4 KPI cards, donut, and the real trend line chart. Click the **Flagged Violations** tab — scroll to a `DUPLICATE_WORK_SUSPECTED` entry to show the side-by-side duplicate comparison. Click **Human Review Queue** tab briefly. | This is the page you must pre-warm (see above) or the numbers will sit at 0 on camera for several seconds. |
| 2:15–2:25 | Forecasting | Click **Explore → ML Dashboard**. Show the **Critical Anomalies by State** table, then scroll right/down to the **6-Month Expenditure Forecast** chart. | The forecast chart also takes a few seconds to compute on first load — let it finish before cutting. |
| 2:25–2:35 | Closing montage | Quick cuts back through: India map (`/`) → risk gauge (project page) → AI explanation card → Compliance dashboard → logo/hero. | Reuse clips already captured above rather than re-navigating live. |

## Why the pre-warm step matters

Two backend computations are genuinely expensive the *first* time they run
after a server restart, then instant for the rest of that server's life:

- **Compliance summary/violations** (`/compliance`): evaluates 7 rules +
  duplicate detection over ~98K rows. Cold: up to ~40s. Warm: 1-3s.
- **6-month forecast** (`/ml-dashboard`): first Prophet/trend computation
  per entity. Cold: a few seconds. Warm: near-instant.

Neither is fake data or a bug — it's real computation with no cache yet.
Just visit both pages once before recording and they'll be fast for the
actual take.

## Demo login

| Role | Email | Password |
|---|---|---|
| Ministry (use this one) | `ministry@nirikshak.demo` | `demo1234` |
| MP | `mp@nirikshak.demo` | `demo1234` |
| State Nodal (UP) | `state.up@nirikshak.demo` | `demo1234` |
| District (Gorakhpur) | `district.gorakhpur@nirikshak.demo` | `demo1234` |

## Local run checklist

```
uvicorn api:app --host 127.0.0.1 --port 8000            # Compliance/Auth API
uvicorn backend.backend_api:app --host 127.0.0.1 --port 8001   # ML/Analytics API
cd frontend && npm run dev                                # http://localhost:3000
```

See `mdfiles/USER_GUIDE.md` for full setup details.
