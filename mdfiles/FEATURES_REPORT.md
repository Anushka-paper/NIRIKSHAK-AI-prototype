# NIRIKSHAK-AI — Feature Report

Complete tabular inventory of implemented features, grouped by module.

## 1. Authentication & Access Control

| Feature | Description | Status |
|---|---|---|
| JWT-based login | Email/password login issuing a signed JWT session token | ✅ Live |
| Role-based access control (RBAC) | 4 personas — MP, State Nodal Authority, District Authority, Ministry — each with a distinct data scope | ✅ Live |
| Server-side scope enforcement | Every request re-validates role/scope against the database, not just at login | ✅ Live |
| Invite-based account provisioning | Ministry creates an account with no password; invitee sets their own via a one-time link | ✅ Live |
| Account activation toggle | Ministry can activate/disable any account; takes effect immediately (no re-login needed) | ✅ Live |
| Demo accounts | One pre-seeded login per role for instant demoing | ✅ Live |

## 2. Dashboard & Overview

| Feature | Description | Status |
|---|---|---|
| National overview dashboard | Role-scoped summary: total works, financial lifecycle, dataset health | ✅ Live |
| Interactive India map | Clickable state polygons/dots, color-coded by computed risk score, real per-state financial + works data | ✅ Live |
| Financial lifecycle chart | Allocated vs. Sanctioned vs. Expenditure bar chart (recharts) | ✅ Live |
| Status donut charts | Completed/Ongoing/Pending breakdowns, reused across Overview, State, and MP pages | ✅ Live |
| Animated stat strip | Landing page KPI counters — only renders when backend data is actually available (no fake fallback numbers) | ✅ Live |

## 3. States & Constituencies

| Feature | Description | Status |
|---|---|---|
| Browse States/UTs | Grid of all 36 states/UTs with completion rate, fund allocation, filtering, search | ✅ Live |
| State detail page | Per-state KPI cards, financial chart, full MP roster, constituency list | ✅ Live |
| Top/Bottom-10 completion comparison | Bar charts ranking states by completion rate | ✅ Live |
| MP performance leaderboard | Ranked, searchable, sortable (by works / completion rate / funds) with a top-10 bar chart | ✅ Live |

## 4. MP Profiles

| Feature | Description | Status |
|---|---|---|
| Individual MP page | Full metrics: total/completed works, sanctioned amount, disbursed amount | ✅ Live |
| Work status donut | Real completed/ongoing/pending breakdown per MP | ✅ Live |
| Completed works gallery | Card/list view of verified completions with search | ✅ Live |

## 5. Projects (Works)

| Feature | Description | Status |
|---|---|---|
| Projects directory | All works, filterable by Lok Sabha / Rajya Sabha | ✅ Live |
| Project detail page | Full feature breakdown, financial lifecycle, timeline | ✅ Live |
| ML delay-risk inference | Runs the trained model live and shows a risk gauge + projected delay + recommended action | ✅ Live |
| SHAP-grounded AI explanation | Plain-language explanation of *why* the model scored a project the way it did | ✅ Live |
| LLM-generated narrative | Real Anthropic API call for natural-language explanation, with a rule-based fallback when unavailable | ✅ Live (fallback verified; live LLM path needs `ANTHROPIC_API_KEY`) |
| Similar-works search | Semantic duplicate search over work descriptions | ✅ Live |
| Per-work PDF dossier | Downloadable compliance dossier for a single work | ✅ Live |

## 6. Compliance Audit

| Feature | Description | Status |
|---|---|---|
| Compliance health score | Aggregate score computed from real rule-check results | ✅ Live |
| Compliance trend chart | Real monthly Compliant/Under-Review/Non-Compliant trend (recharts, replaces earlier static mockup) | ✅ Live |
| All-projects compliance table | Every work with per-rule pass/fail breakdown | ✅ Live |
| Flagged Violations feed | Searchable/filterable feed of every rule violation | ✅ Live |
| Duplicate-work detection | Fuzzy-match + distinguishing-token gate; side-by-side comparison view with similarity score | ✅ Live |
| Human Review Queue | Works flagged `NEEDS_REVIEW`; approve/reject with notes; conflict-of-interest guard (MPs can't review own works) | ✅ Live |
| Compliance Findings | Trackable cases opened automatically on BLOCK-severity violations — assign, add notes, resolve | ✅ Live |
| Compliance Check submission | Submit a new work; runs the full statutory rules engine and returns APPROVED/BLOCKED/NEEDS_REVIEW | ✅ Live |
| Fair violation sampling | Round-robins across rule types so no single rule type dominates the feed | ✅ Live |

## 7. Alerts

| Feature | Description | Status |
|---|---|---|
| Role-scoped risk alerts | Bell icon shows open alerts scoped to the logged-in user's role/jurisdiction | ✅ Live |
| Auto-raised on violation | BLOCK-severity rule failures automatically raise alerts to MP, State Nodal, District, and Ministry | ✅ Live |
| Read/Resolve workflow | Anyone can mark read; resolving requires State Nodal / District / Ministry | ✅ Live |
| Auto-refresh | Polls every 30 seconds | ✅ Live |

## 8. Anomaly Detection

| Feature | Description | Status |
|---|---|---|
| Isolation Forest model | Unsupervised anomaly scoring over fund utilization/billing patterns | ✅ Live |
| Analytics graphs | State breakdown, reason breakdown, risk-band charts | ✅ Live |
| Flagged works table | Searchable table of anomalous works | ✅ Live |
| Honest detection metrics | Real "Detection Rate" — no fabricated accuracy/ROC-AUC (not meaningful for unsupervised models) | ✅ Live |

## 9. ML Dashboard

| Feature | Description | Status |
|---|---|---|
| Anomaly table | Technical view of all flagged anomalies | ✅ Live |
| 6-month forecast chart | Prophet-based (or trend-projection fallback) expenditure forecast | ✅ Live |
| Vendor-collusion graph model | Live counts from the graph-based collusion detector | ✅ Live |
| CSV export | Downloads flagged anomaly data | ✅ Live |

## 10. Admin (Ministry only)

| Feature | Description | Status |
|---|---|---|
| Manage Accounts | Create/list/reinvite/toggle-active for all user accounts | ✅ Live |
| Account stat cards | Total/Active/Invited/Disabled counts | ✅ Live |

## 11. Platform / UX

| Feature | Description | Status |
|---|---|---|
| Fully responsive layout | Mobile hamburger nav, responsive grids, scrollable tables | ✅ Live |
| Global error boundaries | Branded "Something went wrong" and "Page not found" screens | ✅ Live |
| Honest failure states | Every page shows an explicit "data unavailable" message instead of fake/fallback numbers when a backend is down | ✅ Live |
| Nightly model retraining | GitHub Actions workflow re-scrapes data and retrains the delay-risk model automatically | ✅ Live |

---
*See `mdfiles/TECHNICAL_IMPLEMENTATION.md` for the underlying tech stack, and `mdfiles/USER_GUIDE.md` for usage instructions.*
