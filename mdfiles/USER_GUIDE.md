# NIRIKSHAK-AI — User Guide

This guide walks through running the app locally and using every feature as an
end user. For engineering status/gaps, see `mdfiles/PRD_GAP_CLOSURE.md` and
`mdfiles/UI_GAPS_TRACKER.md` instead — this document is about *using* the app,
not its build status.

## 1. What this is

NIRIKSHAK-AI is an AI-powered monitoring platform for MPLADS (Members of
Parliament Local Area Development Scheme) — it tracks fund utilization, flags
compliance violations and anomalies, forecasts risk, and gives four different
government roles (MP, State Nodal Authority, District Authority, Ministry)
their own scoped view of the data.

## 2. Running it locally

The app is three separate processes. Start them in this order, each from the
repo root unless noted:

| Service | Command | Port | What it serves |
|---|---|---|---|
| Compliance API | `uvicorn api:app --host 127.0.0.1 --port 8000` | 8000 | Auth, RBAC, works, alerts, findings, admin |
| ML/Analytics API | `uvicorn backend.backend_api:app --host 127.0.0.1 --port 8001` | 8001 | Overview, states, anomalies, ML predictions, risk explanations |
| Frontend | `npm run dev` (from `frontend/`) | 3000 | The web app |

`frontend/.env.local` should point at both:
```
ML_SERVICE_URL=http://127.0.0.1:8001
BACKEND_API_URL=http://127.0.0.1:8000
```

Then open **http://localhost:3000**.

If you only start one of the two backend services, pages that depend on the
other will show an honest "data unavailable" message rather than fake numbers
— that's expected, not a bug (see `mdfiles/UI_GAPS_TRACKER.md` item 3-4 for why).

### Optional: enabling the LLM risk-explanation feature

The "Get Full AI Explanation" button on a project page needs a real Anthropic
API key. Without one, it automatically falls back to a template-based
explanation over the same underlying data — nothing breaks, you just don't get
the LLM-generated prose. To enable it:
```
export ANTHROPIC_API_KEY=sk-ant-...   # before starting backend_api.py
```

## 3. Logging in

Go to **/login**. Demo accounts (password `demo1234` for all):

| Role | Email | Sees |
|---|---|---|
| Member of Parliament | `mp@nirikshak.demo` | Only their own constituency's works |
| State Nodal Authority | `state.up@nirikshak.demo` | All works in Uttar Pradesh |
| District Authority | `district.gorakhpur@nirikshak.demo` | All works in Gorakhpur district |
| Ministry | `ministry@nirikshak.demo` | Everything, nationally |

Every data-fetching page enforces this scope on the server — an MP can't
widen their view by editing a URL or query parameter.

### Getting a real (non-demo) account

Accounts aren't self-registered. A Ministry user provisions them:
1. Log in as Ministry, go to **Explore → Manage Accounts**.
2. Fill in name, email, role, and scope (pick a real MP from the dropdown for
   the MP role; type a state/district name otherwise).
3. Click **Create account & generate invite** — copy the invite link shown.
4. Share that link with the person. They open it, set their own password, and
   are logged in immediately. Nobody but them ever sees or sets that password.
5. Ministry can toggle any account active/disabled from the same table, and
   resend an invite if it's not yet accepted.

## 4. The navigation

- **Overview** — national (or role-scoped) dashboard: total works, financial
  lifecycle, per-state performance, dataset health.
- **Compliance Audit** — the core compliance workflow (see §5).
- **Explore** dropdown — Browse States, Projects, Anomalies, ML Dashboard, and
  (Ministry only) Manage Accounts.
- **Bell icon** — your open risk alerts (see §6).
- Your name/role and **Log out** are always in the top right.

## 5. Compliance Audit page

Five tabs:

- **Dashboard Overview** — compliance health score, trend chart, AI-detected
  issue categories.
- **All Projects Compliance Status** — every work with its per-rule pass/fail
  breakdown.
- **Flagged Violations** — searchable/filterable feed of every rule violation,
  including duplicate-work pairs shown side by side with a similarity score.
- **Human Review Queue** — works flagged `NEEDS_REVIEW` (ambiguous keyword
  matches); approve or reject with notes. MPs cannot act on their own works
  here (conflict-of-interest rule).
- **Compliance Findings** — trackable cases opened automatically whenever a
  submission trips a BLOCK-severity rule. Assign an officer, add remediation
  notes, and resolve — the resolution-rate KPI in the tab header updates live.

### Submitting a work for compliance checking

Use the **Compliance Check** action (from the dashboard tab) to submit a new
work recommendation. It runs the full statutory rules engine immediately and
returns APPROVED / BLOCKED / NEEDS_REVIEW. A BLOCK-severity result
automatically raises both an alert (bell icon) and a compliance finding.

## 6. Alerts

The bell icon shows open risk alerts scoped to your role — e.g., a District
Authority sees alerts for works in their district; Ministry sees a rollup of
everything. Alerts refresh every 30 seconds. Anyone can mark an alert read;
resolving one requires State Nodal / District / Ministry (not MP).

## 7. Projects

**Explore → Projects** lists all works (filterable by Lok Sabha/Rajya Sabha).
Click into any project for its full feature breakdown, financial lifecycle,
and timeline. Two AI actions live here:

- **Run ML Risk Inference** — queries the trained delay-risk model
  (a real `HistGradientBoostingClassifier`, not a placeholder) and shows a
  risk gauge, projected delay, and recommended action.
- **Get Full AI Explanation** (appears after running inference) — a
  SHAP-grounded explanation of *why* the model scored this work the way it
  did, in plain language. Shows a badge telling you whether it was
  LLM-generated or a template fallback (see §2 on enabling the LLM).
- **Find Similar Works** — semantic duplicate search over the work
  description.

## 8. Anomalies

Two views: **Analytics Graphs** (state breakdown, reason breakdown, risk
bands from the Isolation Forest anomaly model) and **Flagged Works** (a
searchable table). The "Detection Rate" KPI is a real, honestly-computed
figure — there's no fabricated "accuracy" metric shown here, since an
unsupervised anomaly detector has no ground-truth labels to score against.

## 9. ML Dashboard

A technical view of the anomaly table, a 6-month expenditure forecast chart,
and the vendor-collusion graph model's live counts. **Generate Report**
downloads a CSV of flagged anomaly data.

## 10. Browse States

Grid of all states/UTs with completion rates and fund allocation; click into
one for its MP roster, performance graph, and paginated work list.

## 11. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Redirected to `/login` immediately | You're not authenticated — this is correct behavior on every data page except the landing page. |
| A page shows an amber "temporarily unavailable" banner instead of numbers | The backend it depends on isn't running or errored — start/check that service, don't treat the banner as broken UI. |
| "Get Full AI Explanation" always shows "Template fallback" | No `ANTHROPIC_API_KEY` set — see §2. This is intentional graceful degradation, not a bug. |
| A bad/unknown URL | Shows a branded "Page not found" screen with a link back to Overview. |
| An unexpected error while using a page | Shows a branded "Something went wrong" screen with a "Try again" button. |
