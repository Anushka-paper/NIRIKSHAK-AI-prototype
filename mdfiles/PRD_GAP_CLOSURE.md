# PRD — Closing the SIH26102 Gaps in NIRIKSHAK-AI

**Status:** In progress
**Owner:** TBD
**Source:** Gap analysis against SIH26102 problem statement (MPLADS AI Monitoring Platform), 2026-09-12

## 0. Progress tracker

| Item | Status |
|---|---|
| Quick fix: rename mislabeled `fake_images` field | ✅ Done |
| Epic 1 — RBAC & multi-persona dashboards | 🟡 Partial — see Epic 1 notes |
| Epic 2 — Alerting & notification engine | 🟡 Partial — see Epic 2 notes |
| Epic 3 — Real trained risk/delay model | ✅ Done — trained, wired live, browser-verified |
| Epic 4 — Duplicate-work detection | ✅ Done — validated against real dataset |
| Epic 5 — Compliance action-loop | ✅ Done — browser-verified end to end |
| Epic 6 — LLM-grounded risk explanation layer | 🟡 Done except live LLM call untestable — see Epic 6 notes |
| Real MP roster sync (real MPs → admin picker) | ✅ Done — 929 real MPs synced, verified |
| Account status toggle (activate/deactivate) | ✅ Done — browser-verified |
| Navbar redesign (dropdown + dead-link removal) | ✅ Done — see note below |

## 1. Why this document exists

The core data pipeline, anomaly-detection ML, forecasting, and rules engine are already
built and working on real data. What's missing is what a judging panel will check against
the problem statement line-by-line: **role-based multi-persona access**, **actual alerting**,
a **trained (not heuristic) risk predictor**, better **duplicate-work detection**, and a
**closed-loop workflow** so flagged violations lead to a tracked outcome, not just a list.

This PRD sequences those five gaps into shippable epics, ordered by dependency and
demo impact. Each epic is independently mergeable — later epics build on earlier ones
but nothing blocks on all five being done at once.

## 2. Priority order and why

1. **RBAC & multi-persona dashboards** — ships first because every other epic (alerts,
   action-loop) needs to know *who* is looking and *what scope* they're allowed to see.
   Building alerts before roles means rebuilding alert targeting later.
2. **Alerting & notification engine** — the most visible gap in a demo; "the system
   generates alerts" is in the problem statement's second sentence.
3. **Real trained risk/delay model** — currently heuristic; judges reading
   `ML_DOCUMENTATION.md` will see "Pending Training" verbatim. Swap-in, not a rewrite.
4. **Duplicate-work detection (entity resolution)** — currently a raw `.duplicated()`
   check; upgrading it is scoped, high-signal work.
5. **Compliance action-loop (flag → assign → resolve)** — closes the "decision support"
   promise; lower priority because dashboards are already informative without it, but
   it's what turns this from a report into a monitoring *platform*.

## 3. Epic 1 — Role-Based Access & Multi-Persona Dashboards

### Problem
No auth, no user model, no session anywhere in `frontend/src`. `/api/dashboard/{role}/{entity}`
(`backend/backend_api.py:529`) is a stub returning `{"message": "RBAC scope applied"}` with
no actual scoping. There is one public dashboard; the problem statement names four personas
with different data scopes: **MP** (own constituency only), **State Nodal Authority** (own
state, all MPs in it), **District Authority** (own district, cross-MP), **Ministry** (national,
all states).

### Goal
A user logs in, sees a role automatically, and every dashboard query is scoped to what
that role is allowed to see — without four separate codebases.

### User stories
- As an **MP**, I log in and only see my own constituency's works, ledger, and compliance status.
- As a **State Nodal Authority**, I see all MPs and works within my state, with state-level rollups.
- As a **District Authority**, I see all works located in my district regardless of which MP recommended them.
- As a **Ministry** user, I see the full national dashboard (current `overview`/`states` pages, unchanged).

### Functional requirements
- `User` table: `id, email, password_hash, role (enum: MP|STATE_NODAL|DISTRICT|MINISTRY), scope_id` (nullable FK — MP's own mp_id, state name, or district name; null for MINISTRY).
- Login endpoint issuing a signed session token (JWT or server session — pick one, don't build both).
- A `require_role()` / `scoped_query()` dependency in FastAPI that every data endpoint passes through, injecting a `WHERE` filter based on `scope_id` before hitting `backend/backend_api.py` or `api.py` query logic.
- Frontend: a login page, a route guard, and a role-aware nav (hide/show pages by role — an MP shouldn't see `/states` national rollup).
- Ministry role = today's existing unrestricted views, so this is additive, not a rewrite of existing pages.

### Acceptance criteria
- Logging in as an MP and hitting any works/compliance/anomaly endpoint returns **only** that MP's data, even if the query string asks for another MP's ID (server-side enforced, not just hidden in UI).
- A District Authority sees works from multiple MPs whose `work_location_district` matches their district.
- No unauthenticated request can reach a data endpoint (existing public demo mode can stay behind a feature flag for judging convenience, but production path requires auth).

### Technical notes
- Reuse `models.py`'s existing `MP`/`WorkRecommendation` tables; add `User` and a scope-check helper in `db.py`.
- Don't build a full permissions matrix (RBAC libraries, granular per-action ACLs) — four roles, one scope column each, is enough for this problem statement. Resist over-engineering here.

### Effort: Medium (3-5 days). **Priority: P0.**

### Implementation status (2026-09-12)

**Done and verified (backend, `TestClient` smoke-tested end-to-end):**
- `User` model added (`models.py`) with `UserRole` enum (MP/STATE_NODAL/DISTRICT/MINISTRY) and `scope_id`.
- `auth.py`: bcrypt password hashing, JWT issuing/verification (`pyjwt`), `get_current_user` / `require_role` FastAPI dependencies, and `scope_works_query()` — a server-side SQLAlchemy filter applied per role.
- `api.py`: `POST /auth/login`, `GET /auth/me`, and scoping wired into `/works`, `/review-queue`, `/review-queue/{id}/decide`, and `/check-and-submit-work`. Confirmed via test: Ministry sees all works including one from another MP/state; MP/State-Nodal/District each correctly see only their own scope; unauthenticated requests get `401`; an MP cannot submit work under another `mp_id` (`403`); an MP cannot decide their own review queue (`403`, conflict-of-interest guard).
- Demo accounts auto-seeded on startup (`auth.seed_demo_users`) for all 4 roles, password `demo1234` — see `login` page for the list.
- `backend/backend_api.py`'s `/api/v1/compliance/violations` now requires login and forces a STATE_NODAL user's `state` filter to their own scope (can't widen via query param). `/api/v1/compliance/summary` now requires login but is **not yet scoped** — `get_compliance_summary()` has no state/district filter parameter, so all logged-in roles currently see the same national aggregate there. Left as a documented gap rather than faked.
- Root `requirements.txt` was previously missing `fastapi`/`uvicorn`/`sqlalchemy`/`pydantic` entirely (the README's own quick-start would have failed on a clean clone) — fixed alongside adding `bcrypt`/`pyjwt`.
- Frontend: `AuthProvider`/`useAuth` context (`lib/authContext.tsx`), a `/login` page with clickable demo-account prefill, Navbar shows the signed-in user + role + logout, and `useRequireAuth()` redirects unauthenticated visitors. The `/compliance` page and its three data-fetching children (`ComplianceCheckModal`, `HumanReviewQueue`, `WorksComplianceList`) now attach the bearer token, and all six `/api/compliance/*` Next.js proxy routes forward the `Authorization` header through to the backend instead of dropping it.

**Browser-verified live (2026-09-12, headless Chromium via Playwright, both servers actually running):**
- Unauthenticated visit to `/compliance` correctly redirects to `/login`.
- Logging in as Ministry shows "Ministry of Statistics & PI · Ministry" in the Navbar and a fully populated compliance dashboard (75,501 real projects, corrected `vendor_concentration` label, real monthly trend chart).
- Logging in as District Authority (Gorakhpur) shows "Gorakhpur District Authority · District Authority" in the Navbar, the Human Review Queue correctly shows only Work #4 (the Gorakhpur-scoped flagged work) with Approve/Reject controls, and the All-Projects tab shows exactly the 4 Gorakhpur-scoped works with per-work statutory rule-pass counts.
- No console errors on the `/compliance` page itself; the only 502s seen were from `/overview`'s unrelated calls to `backend_api.py` endpoints, which wasn't running in this test (expected — a separate service, not part of this epic).

**Update (2026-09-12): invite-based account provisioning added and browser-verified.**
Registration was originally listed as a gap ("no registration/user-management UI —
accounts are seeded, not self-service"). Built instead of left open, using the standard
institutional pattern: Ministry provisions an account with **no password**, and the
invitee sets their own password via a one-time invite link on first login.
- `models.py`: `User.password_hash` is now nullable; added `invite_token` (unique) and `invite_expires_at`.
- `auth.py`: `create_invited_user()`, `reissue_invite()`, `accept_invite()` (validates token + 7-day expiry, requires an 8+ char password, single-use — consumed on success). `authenticate_user()` now correctly rejects login for an account with no password yet instead of crashing.
- `api.py`: `POST /admin/users` (Ministry-only; validates `scope_id` against a real `mps.id` for the MP role), `POST /admin/users/{id}/reinvite`, `GET /admin/users` (shows Active/Invited status), `GET /admin/mps` (populates the MP picker), `POST /auth/accept-invite`.
- Frontend: `/admin/users` (Ministry-only, nav-gated) — a form to provision an account plus an accounts table with per-user status and a "Resend invite" action; `/accept-invite?token=...` — the invitee's set-password page.
- **Browser-verified live end-to-end**: logged in as Ministry, created a new District Authority account for Varanasi via the admin form, copied the generated invite link, logged out, opened the invite link as a fresh session, set a password, and landed authenticated on `/overview` with the Navbar correctly showing "Varanasi District Authority · District Authority". Confirmed via `TestClient` that: a non-Ministry role gets `403` trying to provision; an invalid `mp_id` scope gets `422`; a duplicate email gets `409`; logging in before accepting the invite gets `401` (not a crash); a too-short password gets `422`; the invite token is single-use (`404` on reuse); and re-inviting an already-active account gets `409`.

**Fix (2026-09-12): toggle switch visually overlapped the status label.** The knob `<span>`
had no explicit `left` offset (only a `translate-x`), so its base position was implicit and
rendered inconsistently; the table also had no responsive overflow handling. Fixed by
adding `left-0.5` to the knob, `shrink-0`/`inline-block` to the switch button,
`whitespace-nowrap` on the status cell, and wrapping the accounts table in
`overflow-x-auto` with a `min-w-[640px]` so columns scroll horizontally instead of
compressing/overlapping at narrow widths. Verified at 1280px — clean spacing, no overlap.
(Noted separately, not yet fixed: the account-creation form's 2-column grid still
overlaps at very narrow (~420px) viewports — a pre-existing, lower-priority responsive
gap on this admin-only page, left for a follow-up pass.)

**Update (2026-09-12): account activate/deactivate toggle added and browser-verified.**
`models.py`: `User.is_active` (default true). `auth.get_current_user()` now re-checks the
account against the DB on every request (not just at login) — this costs one extra query
per request but means a deactivation takes effect immediately, even against a JWT issued
minutes earlier and not yet expired. `POST /admin/users/{id}/toggle-active`
(Ministry-only, refuses to let Ministry deactivate its own account — `400`). Frontend: a
real toggle switch per row on `/admin/users` (disabled for the logged-in Ministry user's
own row). Verified: disabling a user immediately 401s their *already-issued* token on the
very next request (not just blocks future logins), re-enabling restores access, and the
self-lockout guard fires correctly.

**Fix (2026-09-12): parliament filter toggle (All/Lok Sabha/Rajya Sabha) showed stale
data.** Root cause: a real race condition, not a rendering bug — `fetchSummary()`/
`fetchViolations()` fired on every `parliament` change with no guard against out-of-order
responses. Clicking "Lok Sabha" fires a fast, smaller request; if the page's initial "All"
request (larger, slower) was still in flight, its stale response could land *after* and
silently overwrite the correct Lok Sabha numbers with "All" data — reproduced by clicking
the toggle immediately on page load. Fixed with a request-ID guard (`useRef` counter) in
both fetch functions in `frontend/src/app/compliance/page.tsx`: a response is only applied
if no newer request has been fired since. Verified in the exact worst-case scenario
(clicking Lok Sabha the instant the page loads, before the "All" request could possibly
finish) — the UI now correctly settles on the real Lok Sabha numbers (59,653 total / 18,906
compliant / 39,668 under review / 1,079 non-compliant, matching the API exactly) with no
stale overwrite.

**Non-fix (2026-09-12): "Compliance 2.0" reported as still visible in the nav.**
Confirmed via a completely fresh, cookie-less browser context that it is **not** present in
the current code or served page — it was already removed from `Navbar.tsx` earlier this
session. This was a stale browser cache on the reporting user's end, not a code issue; a
hard refresh (Ctrl+Shift+R) resolves it.

**Update (2026-09-12): Navbar redesigned — too many links crammed into one row.**
Reduced the always-visible bar to `Overview` and `Compliance Audit` (the two highest-traffic
pages) plus a single `Explore ▾` dropdown holding `Browse States`, `Projects`, `Anomalies`,
`ML Dashboard`, and `Manage Accounts` (Ministry-only, unchanged). The dropdown highlights
orange when the current page belongs to its group, closes on outside-click and on
selection, and the chevron flips open/closed. Also removed `Compliance 2.0` from the nav
entirely — it pointed at `/compliance-2`, a route that doesn't exist in
`frontend/src/app/` (confirmed no such directory), so it was a dead link doing nothing.
Browser-verified: dropdown opens/closes correctly, navigating to Anomalies via it works
and closes the menu, no console errors.

**Explicitly NOT done yet (remaining Epic 1 work):**
- No email delivery — the invite link is generated and shown directly in the admin UI for the Ministry user to copy/share manually. A real deployment would wire this to an email service.
- Route guards / role-aware nav only cover `/compliance` and `/admin/users`. `overview`, `states`, `mp`, `mps`, `anomalies`, `ml-dashboard`, `projects` are still open pages with no login requirement — a judge or user can view the whole national dataset without signing in via those routes. Rolling `useRequireAuth()` out to each is mechanical but not yet done.
- No registration/user-management UI — accounts are seeded, not self-service. Fine for a hackathon demo, not for real deployment.
- `backend/backend_api.py`'s dataset (the large historical CSV, distinct from the live `WorkRecommendation` demo DB) has no per-district or per-MP-name column wired for scoping yet, so DISTRICT and MP-role users get an unfiltered/best-effort view there, not a true jurisdiction-scoped one. State-level scoping works for STATE_NODAL on the violations endpoint only.
- `JWT_SECRET` defaults to a hardcoded dev string in `auth.py` if the env var isn't set — must be set explicitly before any real deployment.

## 4. Epic 2 — Alerting & Notification Engine

### Problem
Every "risk" today is a row in a dashboard table someone has to go look at. No push
notification, no digest, no way for a District Authority to know a new BLOCK-severity
violation appeared without opening the app.

### Goal
When a rule fires at BLOCK or CRITICAL severity, the right role(s) get notified without
having to poll the dashboard.

### User stories
- As a District Authority, I get notified when a work in my district is flagged CRITICAL by the anomaly model or a BLOCK rule.
- As a Ministry user, I see a daily digest of new high-severity flags across all states.
- As an MP, I get notified when my own submitted work is blocked or sent to review.

### Functional requirements
- An `Alert` table: `id, work_id, rule_code, severity, message, target_role, target_scope_id, created_at, read_at, resolved_at`.
- A hook in `rules_engine.py`'s `engine.evaluate()` call site (`api.py:143`) and in `compliance_engine.py`'s violation loop: any BLOCK/CRITICAL result writes an `Alert` row scoped to the relevant MP/district/state, rolling up to Ministry.
- In-app alert feed (bell icon + panel) reading `Alert` rows scoped to the logged-in user (depends on Epic 1's scoping).
- Email digest (or Slack webhook — pick whichever is faster to demo) for daily CRITICAL summaries, sent via a scheduled job (the existing `nightly_scrape.yml` GitHub Actions pattern can host a second nightly job).
- Do **not** build real-time push (WebSocket/SSE) for v1 — in-app feed on page load + daily email digest satisfies "risk-based alerts" without the added infra complexity.

### Acceptance criteria
- Submitting a work that trips `SocietyEligibilityRule` (BLOCK) creates a visible alert for that MP and their state's Nodal Authority within the same request cycle.
- A District Authority's alert feed only shows alerts scoped to their district (enforced server-side, same pattern as Epic 1).
- Alerts can be marked read/resolved from the UI.

### Effort: Medium (3-4 days). **Priority: P0** (depends on Epic 1 for scoping, but the `Alert` table and rule-hook can be built in parallel).

### Implementation status (2026-09-12)

**Done and verified (backend `TestClient` + live browser, Playwright):**
- `Alert` model added (`models.py`) with `target_role`/`target_scope_id`, `read_at`, `resolved_at`.
- `db.raise_alerts_for_work()` hooked into `api.py`'s `check-and-submit-work`: every BLOCK/CRITICAL rule failure raises one `Alert` row per relevant persona (the work's MP, its State Nodal Authority, its District Authority, and a Ministry rollup row) — confirmed by submitting a work that blows the ₹5 Cr entitlement ceiling and seeing exactly 1 alert appear for MP/State/District each and 4 for Ministry (the full rollup).
- `GET /alerts`, `POST /alerts/{id}/read`, `POST /alerts/{id}/resolve` in `api.py`, all scoped via `db.scope_alerts_query` (mirrors Epic 1's `scope_works_query`). Resolve is restricted to STATE_NODAL/DISTRICT/MINISTRY (confirmed MP attempting to resolve gets `403`).
- Frontend: `AlertBell` component in the Navbar (bell icon + unread badge + dropdown with Mark read / Resolve), polling every 30s, plus 3 new `/api/alerts*` proxy routes forwarding the bearer token. **Browser-verified live**: triggered a real BLOCK alert via the API, watched it appear in the District Authority's bell with the correct message ("Projected sanctioned total Rs.1,009,999,999 EXCEEDS available entitlement Rs.50,000,000"), clicked Resolve, and confirmed it disappeared from the open-alerts list and the badge cleared.

**Explicitly NOT done yet (remaining Epic 2 work):**
- No email/Slack digest — only the in-app feed described above. The PRD's "daily CRITICAL summary" delivery mechanism is unbuilt; would need a scheduled job (cron/GitHub Actions, matching the existing `nightly_scrape.yml` pattern) that queries unresolved alerts and sends a digest.
- Alerts are only raised from `api.py`'s live `check-and-submit-work` path (the `rules_engine.py` domain). `backend/compliance_engine.py`'s historical-dataset violations (the CSV-based audit, used by the `/compliance` dashboard's violations tab) do NOT raise `Alert` rows — they're a pre-existing computed list, not an event stream, so "alerting" on them would mean diffing against a previous run to detect newly-appeared violations, which isn't built.
- Alert bell polls every 30s rather than push/WebSocket — acceptable per the epic's original scope (real-time push was explicitly deferred), but worth calling out as the mechanism.

### Target-state architecture reference (logged 2026-09-12, not yet built)

The user supplied `compliance-alert-system-implementation-plan.md` (repo root) — a full
target architecture for a mature compliance alerting platform: ingestion → rules+ML
detection → alert aggregation/dedup → risk-scored prioritization → multi-channel routing
(Slack/SMS/email/on-call) with escalation chains → case management → analyst
feedback-driven model retraining → immutable audit trail. Logged here so it isn't lost;
read that file for full detail. Comparing it against what Epic 2 actually built:

- **Already covered, smaller scale**: rule-based detection (rules_engine.py +
  compliance_engine.py), an audit trail (`ComplianceCheckLog`, and the `Alert` table's
  `created_at`/`read_at`/`resolved_at`), and role-based routing (an alert is scoped to the
  work's MP/state/district/Ministry, which is this project's version of "route by
  entity/business unit ownership").
- **Explicitly NOT built and likely out of scope for a hackathon timeline**: event
  correlation/deduplication (each rule failure raises its own alert row, no grouping),
  composite priority scoring beyond the rule's fixed severity, multi-channel routing
  (Slack/SMS/on-call — only the in-app bell exists), escalation chains on missed SLA, a
  dedicated case-management/ticketing integration, and an analyst feedback loop for model
  retraining (there's no ML classifier behind these alerts yet — see Epic 3 — so there's
  nothing to retrain from feedback until that exists).
- **Judgment call**: most of this plan's phases (Kafka/Kinesis ingestion, PagerDuty/Opsgenie
  on-call, SHAP-based confidence scoring) describe infrastructure for a production
  financial-compliance platform at a scale well beyond this project's current needs. The
  parts worth pulling forward if there's time after Epics 3-5: (a) confidence/explainability
  metadata on each alert (natural pairing with Epic 6's SHAP-grounded explanations), and
  (b) basic dedup so the same rule firing repeatedly on an unresolved work doesn't spam the
  bell — everything else in this plan should stay aspirational unless the project scope
  genuinely grows toward production deployment.

## 5. Epic 3 — Real Trained Risk/Delay Model (replace heuristic)

### Problem
`/api/v1/predict` (`backend/main.py:303`) uses hardcoded heuristic weights.
`ML_DOCUMENTATION.md` says the delay/risk classifier is "Pending Training" — this is the
single most likely thing a technical judge checks and finds unsupported.

### Goal
Ship an actually-trained binary/multiclass classifier for delay risk, sitting next to the
already-real IsolationForest anomaly model and Prophet forecaster.

### Functional requirements
- Feature set: reuse the existing 118-feature `work_features.csv` (already built, already used by IsolationForest) — no new data engineering needed.
- Label: define "delayed" as `actual_completion_date - sanction_date > COMPLETION_SLA_DAYS` (use the constant already added in `backend/compliance_engine.py`) OR still-incomplete past the SLA — this label is derivable from existing historical data without new annotation.
- Train a gradient-boosted classifier (XGBoost, already referenced as a stub in `ml_models/xgboost_risk_scoring_module.py` — finish, don't rewrite) on historical completed/overdue works; hold out a validation split; report precision/recall, not just accuracy (class imbalance is likely, given a small "delayed" fraction).
- Save as `artifacts/delay_risk_model.joblib`, matching the path `backend/main.py` already tries to load (`ml-service/models/delay_risk_model.joblib` — confirm and align the path, don't add a second one).
- Swap `/api/v1/predict` to load and call this model, with the heuristic kept as a documented fallback only if the model file is missing (e.g., cold start in a fresh clone before training runs).
- Wire retraining into the existing nightly pipeline (`nightly_scrape.yml` → ETL → retrain step) so the model stays current as new scraped data lands — this infra already exists for the forecaster.

### Acceptance criteria
- `ML_DOCUMENTATION.md`'s "Pending Training" line is replaced with real metrics (precision/recall/F1 on a held-out set).
- `/api/v1/predict` response includes a `model_version` or `trained_at` field proving it's not a hardcoded formula.
- Retraining runs nightly and the model file's timestamp updates accordingly.

### Effort: Medium (3-5 days, mostly labeling/validation work — the pipeline plumbing already exists). **Priority: P1.**

### Implementation status (2026-09-12) — Done

**What was discovered first:** `backend/main.py` (a third, currently dormant FastAPI app —
never imported or run by anything, confirmed via repo-wide grep) already had a fully-built
real-model integration for `/api/v1/predict`: model bundle loading, feature-vector
construction, `OrdinalEncoder` application, `predict_proba` inference. But its model
artifact (`ml-service/models/delay_risk_model.joblib`) was **corrupted/version-incompatible**
— attempting to load it threw `ModuleNotFoundError: No module named '_loss'` (an internal
sklearn module renamed between versions). And `ml-service/prediction/delay/{dataset,train,
evaluate,predict}.py` — clearly the intended scaffold for this work — were **all 0 bytes**.
So the real-model plumbing existed in spirit but nothing behind it actually worked.

**What was built:** filled in the empty scaffold for real —
- `dataset.py`: builds the labeled training frame. **Rejected the naive label first**: using
  only completed works' `sanction_to_completion_days > SLA` is heavily survivorship-biased
  (verified: 98.8% of completed works look "LOW risk" this way, because works that are
  *actually* badly delayed just haven't completed yet, so they're invisible to a
  completed-only label). Replaced with a censored/hazard-style label: completed-on-time (0),
  completed-late (1), or *currently open past the 18-month SLA without completing* (1) —
  still-open-and-within-SLA rows are correctly excluded as censored/unknown rather than
  mislabeled either way. This produced a real, usable 78%/22% on-time/delayed split (24,101
  labeled rows) instead of a near-useless 98.8%/1.2% one.
- Feature set deliberately excludes anything only knowable after sanction (completion
  amounts, lifecycle status, execution duration) to avoid leakage — see `dataset.py`'s
  docstring for the exact boundary.
- `train.py`: trains a `HistGradientBoostingClassifier` (matching what `backend/main.py`'s
  dormant code already claimed to use, so that existing integration becomes true rather
  than aspirational) with `OrdinalEncoder`'d categoricals, stores per-feature medians in the
  bundle for imputing fields a live caller doesn't know.
- `evaluate.py`: precision/recall/F1 **per class** (not just accuracy, given the class
  imbalance) plus ROC-AUC and a confusion matrix.
- `predict.py`: single inference entry point, returns `None` (not a crash or a fabricated
  number) if the model artifact is missing.

**Real held-out metrics** (4,821 test rows): accuracy 95.15%, ROC-AUC 0.9899, delayed-class
precision 0.910 / recall 0.868 / F1 0.888. Full metrics in
`ml-service/models/delay_risk_model_metrics.json`.

**Wired into the live service** — `backend/backend_api.py`'s `/api/v1/predict` (confirmed
this is the endpoint the frontend actually calls; `backend/main.py` is not live) now calls
the trained model first. If a real `work_id` is supplied, it looks up that work's actual
historical features from `work_features.csv` for a much more accurate prediction than
guessing from just cost/state/category. The old hash-seeded pseudo-random logic is kept
**only** as a fallback if the model artifact is missing — confirmed by temporarily removing
the `.joblib` file and verifying the endpoint still returns a valid response, clearly
labeled `"model_engine": "heuristic (fallback...)"` so a consumer can always tell which path
served the response. Since the model is sanction-time-only (no live elapsed-time input, to
avoid the leakage a naive "days already elapsed" feature would introduce — see `predict.py`'s
docstring), a transparent, separately-labeled statutory-SLA-overdue override is layered on
top for the live "already running longer than 18 months" case, rather than pretending the
ML score accounts for something it structurally can't see from a single historical snapshot.

**Browser-verified live end to end**: opened a real project detail page
(`/projects/CW_LO_006138`), clicked "Run ML Risk Inference", and got a real result — LOW
RISK, 100% confidence, "On Schedule" — with the Explainable-AI panel correctly citing
"Model: HistGradientBoostingClassifier trained on 24,101 real historical works
(v20260912-113534)". This UI path (`projects/[id]/page.tsx` → `predictRisk()` →
`/api/ml/predict` → `backend_api.py`) is live-used code, not dead state.

**Also done**: nightly retraining wired into `.github/workflows/nightly_scrape.yml` (a new
non-fatal step — a bad nightly retrain degrades to the last good model / fallback heuristic
rather than breaking the pipeline); `mdfiles/ML_DOCUMENTATION.md`'s "Pending Training" line
replaced with the real metrics and label-design rationale.

**Explicitly not done**: Epic 6's SHAP-based per-prediction explainability (the "Key Risk
Drivers" panel currently shows a static "trained on N works" line, not per-prediction
feature attributions) — that's Epic 6's job specifically, and needs this model to exist
first, which it now does.

## 6. Epic 4 — Duplicate-Work Detection (entity resolution)

### Problem
`DUPLICATE_PAYMENT_PATTERN` in `backend/compliance_engine.py` is a raw `df.duplicated()`
check — it only catches byte-identical rows, missing the realistic fraud pattern of the
same work resubmitted with slightly different wording, amount, or district spelling.

### Goal
Flag works that are *likely* duplicates even when not textually identical.

### Functional requirements
- Blocking key: same MP + same financial year + similar sanctioned amount (within a tolerance band, e.g. ±5%).
- Similarity check on `work_description` using a lightweight approach already available in the repo's dependency surface (`sentence_bert_model.py` is referenced as a stub — use sentence-embedding cosine similarity if that module is real; otherwise fall back to fuzzy string matching (e.g. token-set ratio) rather than adding a new heavy dependency for a hackathon timeline).
- New rule `DUPLICATE_WORK_SUSPECTED` (severity HIGH) added to `COMPLIANCE_RULES` in `backend/compliance_engine.py`, following the same pattern as existing rules — no new rule *engine*, just a smarter check inside the existing one.
- Surface duplicate pairs (not just a count) in the violations feed so a reviewer can see both works side by side.

### Acceptance criteria
- Two works from the same MP, same year, with descriptions like "Construction of community hall in Ward 5" and "Community hall construction, Ward-5" and near-identical amounts are flagged as suspected duplicates.
- False-positive rate is sane enough for a demo — validate against the real historical dataset (~75K works) and manually sample flagged pairs before shipping.

### Effort: Small–Medium (2-3 days). **Priority: P1.**

### Implementation status (2026-09-12) — Done

**What was built:** `backend/compliance_engine.py` gained `_detect_suspected_duplicates()`,
called as "Rule 8" inside `evaluate_compliance_violations()`. New `DUPLICATE_WORK_SUSPECTED`
entry in `COMPLIANCE_RULES` (severity HIGH). Blocking key: same MP + same
`sanction_financial_year` + sanctioned amount within 5%. Text similarity: `rapidfuzz`
`token_set_ratio` over a normalized (lowercased, punctuation-stripped) description —
chosen because it's order/duplicate-word-insensitive, added to `requirements.txt` and
`backend/requirements.txt`.

**The real finding from validating against the actual ~75K-row dataset (not skipped, per
the acceptance criteria): the naive version was unusable.** A pure `token_set_ratio >= 85`
threshold flagged 35 candidate pairs, and manually sampling them showed the overwhelming
majority were false positives — MPLADS work descriptions are extremely boilerplate
("solar street light at X", "smart boards for school Y"), so two *genuinely different*
works in different villages/wards routinely score 85-97 on pure fuzzy similarity, since
the only differing content is the place name buried in an otherwise identical sentence.
Neither `token_sort_ratio` nor plain `ratio` discriminated better (tested; the real true
positive actually scored *lower* on plain `ratio` than the false positives did, because it
happened to be more reordered).

**Fix:** added a second, independent gate — `_distinguishing_token_diff()` — that counts
non-stopword tokens appearing in only one of the two descriptions. Verified on real flagged
pairs: the genuine duplicate scored 0 (fully overlapping vocabulary after normalization);
every real false positive scored ≥2 (a differing place name is 1-3 distinguishing words on
each side). Gating on `diff <= 1` in addition to the fuzzy-score threshold dropped the
real-dataset result from 35 candidates to 3 — and all 3 remaining are genuinely suspicious:
three near-identical "purchase of books for school public library" works from the same MP
at the exact same ₹473,826 sanctioned amount.

**Verified:**
- The PRD's own acceptance-criteria example ("Construction of community hall in Ward 5" vs
  "Community hall construction, Ward-5", near-identical amount) is correctly flagged at
  100% similarity, diff=0; an unrelated third work in the same synthetic MP/FY group is
  correctly excluded.
- Full dataset scan (75,501 rows) completes in under 1 second.
- Confirmed live through both HTTP paths: `backend/backend_api.py`'s
  `/api/v1/compliance/violations?rule_code=DUPLICATE_WORK_SUSPECTED` (auth-protected, per
  Epic 1) and `api.py`'s equivalent endpoint both return the same 3 real candidate pairs.
- Each violation carries `duplicate_of_work_id`, `duplicate_of_description`, and
  `similarity_score` fields (beyond the standard violation shape) so a reviewer can see
  both works side by side, per the acceptance criteria.

**Update (2026-09-12): the missing violations-feed UI has been built.** Added a new
"Flagged Violations" tab to `/compliance` (`frontend/src/app/compliance/page.tsx`) that
wires up the `filteredViolations`/`searchQuery`/`severityFilter`/`ruleFilter` state that
already existed but was never rendered — a search box, severity dropdown, and a rule-code
dropdown (populated dynamically from whatever rule codes are actually present), each
violation rendered as a card with severity/category badges. `DUPLICATE_WORK_SUSPECTED`
entries get special side-by-side rendering (Work A description | Work B description, with
the match %) instead of the generic single-description layout other rules use.

**A second real bug surfaced while wiring this up and was fixed, not worked around.** The
default fetch (`limit=200`, no rule filter — what the UI actually calls) returned **zero**
`DUPLICATE_WORK_SUSPECTED` results despite the backend detection working correctly. Root
cause: `evaluate_compliance_violations()` has 2,745 total violations across 8 rules; Rules
1-5 have no per-rule cap and dominate insertion order, so a plain `violations[:limit]`
slice returned only `FINANCIAL_PHYSICAL_MISMATCH` and `EXP_EXCEEDS_SANCTION` — every rule
appended later (including the new duplicate-detection rule) was silently truncated away
before it ever reached the client, regardless of how correct the detection logic was.
Fixed with `sample_violations_fairly()` in `compliance_engine.py` — round-robins across
rule-code groups instead of slicing in insertion order — applied in both `api.py`'s and
`backend/backend_api.py`'s violations route handlers (they duplicate this logic). Verified:
the same default fetch now returns a representative mix of all 5 rule types actually
present in the data, `DUPLICATE_WORK_SUSPECTED` included.

**Browser-verified end to end:** the "Flagged Violations" tab shows a `200` count badge;
filtering the rule dropdown to `DUPLICATE_WORK_SUSPECTED` renders exactly the 3 real
library-book duplicate pairs side by side with correct match percentages, MP/district/
amount; searching "library" correctly surfaces the matching card. No console errors.

## 7. Epic 5 — Compliance Action-Loop (flag → assign → resolve)

### Problem
Every dashboard today is read-only. A flagged violation has no owner, no status beyond
"exists in a list," and no record of what was done about it — undermining the
"decision-support" and "timely corrective action" language in the problem statement.

### Goal
A flagged violation becomes a trackable case: assigned to a role/scope, actioned, and closed with a reason.

### Functional requirements
- Reuses the `HumanReviewQueue` component and `review-queue`/`decide` endpoints already
  built in `api.py` (`/review-queue`, `/review-queue/{work_id}/decide`) — this epic
  **extends** existing code rather than building fresh.
- **Update (2026-09-12): the data model for this already exists.** `models.py` has a
  `ComplianceFinding` table with `assigned_officer`, `status` (OPEN/IN_REMEDIATION/RESOLVED),
  `required_action`, `deadline_date`, `resolved_at`, and `remediation_notes` — it's defined
  but currently has no endpoints or UI reading/writing it. This epic is now mostly wiring,
  not schema design: build the CRUD endpoints and dashboard views on top of the table
  that's already there, rather than extending `ComplianceCheckLog`/the decide-endpoint as
  originally scoped.
- Extend the existing decide-endpoint's outcome enum beyond approve/reject to include
  `assigned_to`, `action_taken`, `resolution_notes`, `resolved_at` (or, per the note above,
  create findings against `ComplianceFinding` directly when a rule fails BLOCK/CRITICAL).
- Dashboard view per role (depends on Epic 1): a District Authority sees cases assigned
  to their district; Ministry sees an aggregate resolution-rate KPI across states.
- Status transitions logged to `ComplianceCheckLog` (table already exists in `models.py`) for audit trail — no new audit table needed.

### Acceptance criteria
- A BLOCK/CRITICAL flag can be assigned to a specific role/scope and its status (open → assigned → resolved) is visible on that role's dashboard.
- The Ministry dashboard shows a resolution-rate metric (e.g., "82% of flags resolved within SLA") computed from real `resolved_at` timestamps, not fabricated.

### Effort: Medium (3-4 days). **Priority: P2** (do last — it depends on Epic 1's roles and benefits from Epic 2's alerts already existing to notify assignees).

### Implementation status (2026-09-12) — Done

**What was built**, extending `ComplianceFinding` (already existed in `models.py`) rather
than inventing a new schema, per the earlier discovery in Epic 1's session:
- `db.seed_compliance_controls()`: populates `ComplianceControl` directly from
  `rules_engine.DEFAULT_RULES` (11 statutory rules) instead of a disconnected invented
  "C001-C010" numbering — every finding's `control_id` traces back to a real rule with its
  actual para reference and severity.
- `db.raise_findings_for_work()`: opens a `ComplianceFinding` for every BLOCK-severity rule
  failure at submission time (same trigger point as Epic 2's `raise_alerts_for_work`),
  assigned by default to `"{district} District Authority"`, with a 30-day remediation
  deadline. Idempotent — re-checking the same work doesn't duplicate the finding.
- `db.scope_findings_query()`: same role/scope rules as `scope_works_query`, joined through
  `work_id` since a finding has no jurisdiction fields of its own.
- `api.py`: `GET /findings` (scoped, optional status filter), `POST
  /findings/{id}/assign`, `POST /findings/{id}/resolve` — both restricted to
  STATE_NODAL/DISTRICT/MINISTRY (MP excluded, same conflict-of-interest reasoning as the
  review-queue decide endpoint), and `GET /findings/resolution-rate` — a real KPI computed
  from actual `resolved_at` timestamps (not fabricated), scoped per role.
- Frontend: a new "Compliance Findings" tab on `/compliance`
  (`ComplianceFindings.tsx`) showing open/resolved findings with severity, status, assigned
  officer, deadline (with an OVERDUE badge when passed), and inline assign/resolve controls
  for the roles allowed to act — plus the resolution-rate KPI in the tab header.

**Browser-verified live end to end**: submitted a work that trips the entitlement-ceiling
BLOCK rule, confirmed a real finding (`MPL-5-FIN_ENTITLEMENT_CEILING`) appeared in the
District Authority's Compliance Findings tab with the correct problem summary, work
reference, and 30-day deadline; assigned it to "Inspector Sharma" (status flipped to IN
REMEDIATION live); resolved it with remediation notes (status flipped to RESOLVED,
resolved-date shown, notes rendered); resolution-rate KPI updated from "0% resolved (0/1)"
to "100% resolved (1/1)" in real time. Backend confirmed via `TestClient`: MP correctly
blocked (`403`) from assigning/resolving their own flagged work; re-resolving an
already-resolved finding correctly rejected (`409`).

## 7a. Epic 6 — LLM-Grounded Risk Explanation Layer

**Status: spec captured, not yet built.** Full build spec received from the user as
`llm_risk_explanation_build_prompt (1).txt` (repo root) on 2026-09-12 — logged here so it
isn't lost before implementation starts. Read that file for the complete, detailed spec;
this section is a summary.

### Problem
Epic 3's risk/delay model (and the existing IsolationForest anomaly scores) produce a
number and, with SHAP, per-feature contributions — but a District Authority or Ministry
reviewer sees a score, not a reason. Nothing today explains *why* a work was flagged in
language a non-technical reviewer can act on.

### Goal
An LLM layer that composes natural-language explanations and proportionate recommended
actions **over already-computed, already-grounded SHAP output** — it never scores risk or
invents facts, only reasons in language about fixed structured evidence. This preserves
explainability: the score and feature attributions are unchanged and fully auditable: the
LLM's only job is prose composition, not decision-making.

### Key design points (from the full spec)
- `build_grounding_payload()` assembles the *only* facts the LLM may reference: risk_score,
  risk_band, SHAP feature contributions (name/value/shap value/direction), the peer
  baseline used for comparison (median, 90th percentile, baseline_version, n_obs — so a
  thin sample is visible to the model), and raw work facts (sanction_amount, vendor_id,
  sanction_date, progress_pct, evidence_on_file).
- LLM call via the Anthropic API using **forced structured output through tool use** — a
  `risk_explanation` tool schema returning `{why: string[], recommended_actions:
  {action, rationale}[], confidence_note: string}`.
- System prompt requires: only reference facts/numbers present in the payload (quoting
  actual figures); reason about interaction effects when multiple features are significant
  together (e.g., cost deviation + vendor concentration compounding is a stronger, different
  story than either alone); keep recommended actions proportionate to the actual driving
  feature; explicitly flag low-confidence situations when baseline `n_obs` is small; **never
  use the word "fraud"** — only "risk indicator," "warrants review," or "requires
  verification" (a real compliance-tool concern, not cosmetic — this may be shown to
  auditors and Ministry officials).
- **Caching**: key on `(work_id, model_version, baseline_version)`; only regenerate when a
  version actually changed; store the full grounding payload alongside the generated
  explanation for audit traceability.
- **Rule-based fallback**: a template-based, non-LLM version of the same output shape, used
  automatically on LLM failure, timeout, or a too-thin payload — must degrade gracefully,
  never return a blank/error state to the frontend.
- **Post-response validation**: every numeric claim in the `why` array must be checked
  against the grounding payload's serialized values before being accepted; a failed check
  falls back to the rule-based version rather than serving an unverified claim.
- Entry point: `get_risk_explanation_safe()` — a single cached + fallback-wrapped call,
  meant to sit directly behind `GET /api/works/{work_id}/risk-explanation`.

### Dependencies
- Needs Epic 3's trained model (or the existing IsolationForest scores) plus a SHAP
  `TreeExplainer` producing per-prediction feature contributions — build this after (or
  alongside) Epic 3, not before, since there's nothing grounded to explain yet otherwise.

### Effort: Medium-Large (the spec itself estimates a full module: grounding, LLM call,
caching, fallback, and validation, each as separate testable functions). **Priority:
unscored yet — sequence after Epic 3.**

### Implementation status (2026-09-12) — built and tested except the live LLM call itself

Discovered `ml-service/genai/{context,prompts,investigation}.py` and
`ml-service/explainability/shap.py` already existed as empty (0-byte) scaffolds, and the
existing `shap.py` stub returned a hardcoded fake `{"top_features": [...]}` regardless of
input. Filled in real content, plus added real SHAP explainability to Epic 3's model first
(`predict.explain_delay_risk()`, using `shap.TreeExplainer` — confirmed it supports
`HistGradientBoostingClassifier`) since Epic 6 has nothing to explain without it.

**What was built:**
- `ml-service/prediction/delay/predict.py`: `explain_delay_risk()` returns real per-feature
  SHAP contributions (feature, value, shap_value, direction), sorted by |impact|.
- `ml-service/prediction/delay/dataset.py`: `compute_peer_baseline()` — real median/p90/n_obs
  per work category from the actual training data, not fabricated, so a thin sample (e.g. a
  rare category with 8 historical peers) is honestly visible rather than papered over.
- `ml-service/genai/context.py`: `build_grounding_payload()` — assembles only
  work_id/risk_score/risk_band/SHAP contributions/peer_baseline/work_facts; nothing else
  reaches the model.
- `ml-service/genai/prompts.py`: the tool schema (`risk_explanation`, forced via
  `tool_choice`) and system prompt enforcing all 5 spec rules (only cite payload facts;
  reason about feature interactions; proportionate actions; flag thin baselines below
  `THIN_SAMPLE_THRESHOLD=30`; never say "fraud").
- `ml-service/genai/investigation.py`: `generate_risk_explanation()` (the actual Anthropic
  API call — model updated from the spec's "claude-sonnet-4-6", which doesn't exist, to the
  current flagship `claude-sonnet-5`), `validate_response()` (regex-extracts every number
  from the LLM's `why` claims and checks it against the payload's flattened numeric values
  within 2% tolerance, in both raw and ×100 percentage form), `rule_based_fallback()`
  (deterministic template over the same SHAP data), and `get_risk_explanation_safe()` — the
  cached, fallback-wrapped one-line entry point, matching the spec's required signature.
- `models.py`: new `RiskExplanation` cache table, keyed on `(work_id, model_version)` —
  `work_id` is a plain indexed string (not an FK), since Epic 3's model predicts over the
  historical CSV dataset's `canonical_work_id`, a different ID space from the small demo
  DB's integer-keyed `WorkRecommendation` table.
- `backend/backend_api.py`: `GET /api/works/{work_id}/risk-explanation` — looks up the real
  work, runs prediction + SHAP + peer baseline, builds the grounding payload, calls
  `get_risk_explanation_safe()` against a real DB session.
- Frontend: a new "Grounded Risk Explanation (SHAP + LLM synthesis)" panel on the project
  detail page (`projects/[id]/page.tsx`) with a "Get Full AI Explanation" button, rendering
  the `why` bullets, recommended actions, and confidence note, with a visible
  LLM-generated-vs-template-fallback badge.

**Real bug found and fixed while wiring this up**: the first live call 500'd with `Object
of type int64 is not JSON serializable` — pandas/numpy scalar types from the CSV row weren't
being converted to native Python types before being cached as JSON. Fixed in both
`backend_api.py`'s endpoint and `predict.py`'s `explain_delay_risk()`.

**Verified (fully, for everything except the live Anthropic call):**
- `investigation.py`'s own runnable `__main__` example (per the spec's deliverable
  requirement) runs three scenarios end-to-end: a normal payload, a thin-baseline payload
  (asserts the confidence-note flag is present), and a simulated LLM network failure
  (asserts the fallback engages and never returns a blank result).
- `validate_response()` tested directly: correctly rejects a fabricated number not present
  in the payload, correctly accepts a real grounded number.
- The full cache flow tested against a real SQLite session: first call for a given
  `(work_id, model_version)` computes and stores (`cached: false`); second call returns the
  identical stored content without recomputing (`cached: true`).
- **Browser-verified live end to end**: opened a real project, ran ML inference, clicked
  "Get Full AI Explanation", and got a real result grounded in that specific work's actual
  SHAP values ("vendor historical completion rate (value: 0.304) increases predicted delay
  risk (model attribution: +1.18)"), correctly labeled "Template fallback (LLM unavailable)
  · cached".

**Explicitly NOT verified — no `ANTHROPIC_API_KEY` is available in this environment.** The
`generate_risk_explanation()` function itself (the actual API call, tool-use request
shape, and response parsing) has never executed against the real Anthropic API in this
session — every test exercised the fallback path, which is the honest, correct behavior
when the key is absent, not a workaround. The code is written against the documented
Messages API (`tools` + forced `tool_choice`), and the surrounding validate/cache/fallback
scaffold around it is fully tested, but the live call path itself needs verification with a
real key before relying on it in a demo where the LLM path specifically needs to be shown
working (as opposed to the fallback, which is equally real functionality but a different
thing to demonstrate).

## 8. Explicitly out of scope for this pass

- Real document/image fraud verification. (The "fake_images" mislabel was fixed —
  `backend/compliance_engine.py` and `frontend/src/app/compliance/page.tsx` now call
  this field `vendor_concentration`, matching what it actually measures. Building real
  image forensics remains a separate, much larger effort not covered here.)
- Real-time push (WebSocket) alerting — daily digest + in-app feed is sufficient for v1.
- Granular per-action permission matrices — four roles with a single scope column each is enough.

## 9. Sequencing summary

| Order | Epic | Priority | Effort | Depends on |
|---|---|---|---|---|
| 1 | RBAC & multi-persona dashboards | P0 | Medium | — |
| 2 | Alerting & notification engine | P0 | Medium | Epic 1 (for scoping) |
| 3 | Real trained risk/delay model | P1 | Medium | — (parallelizable with 1-2) |
| 4 | Duplicate-work detection | P1 | Small–Medium | — (parallelizable with 1-2) |
| 5 | Compliance action-loop | P2 | Medium | Epics 1 & 2 |

Epics 3 and 4 have no dependency on 1/2 and can be built in parallel by a second
contributor while roles/alerts are underway — useful if this is a multi-person team
racing a hackathon deadline.

## 10. Success metrics (for the demo / judging)

- A judge can log in as each of the 4 roles and see visibly different, correctly scoped data.
- A BLOCK-severity violation triggers a visible alert within the same session, no page refresh needed to discover it existed.
- `ML_DOCUMENTATION.md` shows real precision/recall numbers, not "Pending Training."
- At least one true-positive duplicate-work pair from the real dataset is shown flagged in the UI.
- At least one flagged violation can be walked through end-to-end: flagged → assigned → resolved, with the trail visible on the Ministry dashboard.
