# UI Gaps Tracker — NIRIKSHAK-AI Frontend

**Status:** In progress
**Source:** UI audit across all 15 pages in `frontend/src/app`, 2026-09-12 (see conversation
history / `mdfiles/PRD_GAP_CLOSURE.md` for the broader feature-completeness work this sits
alongside).

## Progress tracker

| # | Item | Status |
|---|---|---|
| 1 | Auth gate rollout to remaining 11 public pages | ✅ Done — browser-verified both directions |
| 2 | Global `error.tsx` + `not-found.tsx` | ✅ Done — browser-verified both |
| 3 | Landing page (`/`) — fake data fallback, no error state | ✅ Done — browser-verified both paths |
| 4 | `/anomalies` — hardcoded KPI fallbacks + fake "ROC-AUC"/"Model Accuracy" strings | ✅ Done — browser-verified |
| 5 | `/ml-dashboard` — style outlier (different design system) | ✅ Done — browser-verified |
| 6 | `/ml-dashboard` — hardcoded "System Active" badge | ✅ Done — now reflects real API health |
| 7 | `/ml-dashboard` — "Generate Report" downloads .csv content as .json filename | ✅ Done |
| 8 | Silent-failure secondary data (state MP roster, mps "All Works", ml-dashboard summary) | ✅ Done — browser-verified no false positives |
| 9 | Responsive `grid-cols-2` fallbacks (overview KPIs, states strip, project financials) | ✅ Done — browser-verified at 390px |
| 10 | Minor: color-only badges, dead unused fields | ✅ Done |

## Priority order and why

1. **Auth gate rollout** first — everything else is cosmetic if the whole dataset is
   publicly reachable regardless of login. Mechanical but the highest-impact fix.
2. **Global error/404 boundaries** — cheap, prevents every other bug in this list (and any
   future one) from surfacing as a raw crash screen instead of something graceful.
3. **Fake-data fallbacks** (items 3-4) — these actively mislead a viewer into thinking
   broken data is real, which is worse than an honest "failed to load" state. Same category
   of bug already fixed once this session on the compliance dashboard; closing the same gap
   everywhere else.
4. **`/ml-dashboard` fixes** (5-7) — visible, demoable page; the style mismatch and the
   broken report-download filename are both things a judge could stumble into directly.
5. **Silent-failure states / responsive / minor** — real but lower-visibility polish, done
   last as time allows.

---

## 1. Auth gate rollout

### Problem
Only `/compliance`, `/login`, `/admin/users`, `/accept-invite` call `useAuth`/
`useRequireAuth`. `/`, `/overview`, `/states`, `/states/[slug]`, `/mp/[name]`,
`/mps/[name]`, `/anomalies`, `/ml-dashboard`, `/projects`, `/projects/[id]` are fully public.

### Plan
Add `useRequireAuth()` (already built in `lib/authContext.tsx`) to each remaining page,
same pattern as `/compliance`. Landing page (`/`) is a judgment call — it's a marketing/
entry page, not a data page, so it likely stays public with only its "Explore Projects"
link gating at the destination rather than the landing page itself.

### Status: Done (2026-09-12)

Added `useRequireAuth()` to `/overview`, `/overview/state/[id]`, `/states`, `/mps/[name]`,
`/anomalies`, `/ml-dashboard`, `/projects`, `/projects/[id]` — each page's data-fetching
`useEffect`(s) also gated on `user` so no unauthenticated fetch fires before the redirect
completes. `/mp/[name]` and `/states/[slug]` are pure server-side redirect stubs forwarding
to `/mps/[name]` and `/overview/state/[id]` respectively, so gating the destination page was
sufficient. Landing page (`/`) deliberately left public — it's the marketing/entry page, not
a data page.

**Browser-verified both directions**: a fresh, logged-out session hitting `/overview`,
`/states`, `/anomalies`, `/ml-dashboard`, `/projects` all correctly redirect to `/login`; the
same pages after logging in as Ministry stay on the requested URL and render normally.

**Bonus fixes made while in `/ml-dashboard`**: the "System Active" badge was a pure
decoration with no real signal behind it — now tracks whether the anomalies-summary fetch
actually succeeded and shows "Backend Unreachable" in red if not. Also fixed "Generate
Report": the button fetched `format=csv` but named the downloaded file `.json` — now
correctly named `.csv`.

---

## 2. Global error/404 boundaries

### Problem
No `error.tsx`, `global-error.tsx`, or `not-found.tsx` anywhere in `src/app`. Any unhandled
exception or bad route shows Next.js's raw default screen.

### Plan
Add `frontend/src/app/error.tsx` (client component, catches render errors within the root
layout) and `frontend/src/app/not-found.tsx`, styled consistently with the rest of the app
(rounded cards, orange primary, `font-headline`).

### Status: Done (2026-09-12)

Both added, styled consistently (rounded-2xl card, orange primary button, `font-headline`),
Navbar stays intact around both since neither is a `global-error.tsx` (which would replace
the whole HTML document — not needed here since our root layout itself doesn't throw).

**Browser-verified both, for real, not just by inspection:**
- `not-found.tsx`: visited a nonexistent route, got the branded "Page not found" card with
  a working "Back to Overview" link — not Next.js's raw default 404.
- `error.tsx`: created a temporary throwaway page that deliberately threw an `Error` on
  render, confirmed the branded "Something went wrong" card appears (with "Try again" /
  "Back to Overview" actions and the dev-mode error message), then deleted the temporary
  page. First attempt at this test actually surfaced a real Next.js convention I'd missed —
  a route folder named with a leading underscore (`__test-error-boundary`) is a reserved
  "private folder" excluded from routing entirely, so it 404'd instead of erroring; renamed
  without the underscore and the boundary caught it correctly.

---

## 3. Landing page fake data + no error state

### Problem
`frontend/src/app/page.tsx` (a server component) had hardcoded fallback numbers
(`|| 875`, `|| 35`, `|| 12`, `|| 6`) presented as live stats whenever the backend fetch
failed — no visible error state at all. **Double fake-data layer found**: the `StatStrip`
component it renders also had its own separate hardcoded default props (2715/37/124/11),
a second, redundant landmine that would silently reintroduce fake numbers if any future
caller omitted a prop.

### Status: Done (2026-09-12)

Added a `statsAvailable` flag (true only if both backend calls actually succeeded) and
made the fallback numbers honestly `0` instead of specific fake figures; the stat strip
only renders when `statsAvailable` is true, otherwise an amber warning banner ("Live
statistics are temporarily unavailable — the analytics backend didn't respond") renders
instead. Removed `StatStrip`'s own hardcoded default props entirely, making all 4 stat
props required — a future caller can no longer accidentally render fake numbers by
omitting one.

**Browser-verified both paths for real** (not just by reading the code): with the backend
healthy, the strip shows real live numbers (₹406 Cr / 98,003 / 0 / 36 — matching the actual
backend data, replacing the old fake 875/35/12/6). Then deliberately killed the
`backend_api.py` process, reloaded, confirmed the amber banner appeared instead of any
number, and immediately restarted the backend.

## 4. `/anomalies` fake KPI cards

### Problem
Header badge hardcoded "ROC-AUC 0.8972"; 4th KPI card hardcoded "Model Accuracy 93.8%" /
"ROC-AUC: 0.8972 (Robust)"; other 3 KPI cards fell back to specific fake numbers
("98,003"/"4,901"/"860") on fetch failure. Checking the real `/api/v1/anomalies/summary`
response directly found **no accuracy/ROC-AUC/precision field exists in the API at all** —
these were fabricated from the start with nothing to wire up. Worse, the fake fallback
"860" for critical anomalies had drifted from the real current value (1,268) — a stale
fake number silently presented as current.

Also: IsolationForest is **unsupervised** — there's no ground-truth fraud label in this
dataset to legitimately compute accuracy/ROC-AUC/precision against in the first place, so
this metric couldn't be made real even by wiring up a backend endpoint; it's conceptually
invalid for this algorithm, not just missing.

### Status: Done (2026-09-12)

Removed the fabricated ROC-AUC/accuracy/precision claims entirely. Header badge now reads
"Active Isolation Forest Model (unsupervised)" instead of a fake metric. The 4th KPI card
now shows the "Detection Rate" (flagged &divide; evaluated) — real, honestly computable
from the same data already loaded — instead of "Model Accuracy". The other 3 KPI cards and
the contamination-rate label now show "--" / "Summary unavailable" / "Rate unavailable"
instead of specific fake numbers when the fetch fails, via a `summaryLoaded` flag.

**Browser-verified with the live backend**: "Works Evaluated" 98,003, "Anomalies Detected"
4,901, "Critical High Risk" **1,268** (the real current figure, correcting the stale fake
"860"), "Detection Rate" 5.0% — all real, all honestly labeled.

## 5. `/ml-dashboard` style overhaul

### Problem
Used indigo/gray-50/`rounded-lg` and a different type scale from every other page's
orange-primary/`rounded-2xl-3xl`/`font-headline` design language — looked like a different
app pasted in.

### Status: Done (2026-09-12)

Rewrote the header card, health badge, report button, and the bottom "Vendor Collusion
Graph" panel to match the rest of the app (`bg-white rounded-3xl border shadow-subtle`,
`bg-primary`/`hover:bg-[var(--color-primary-hover)]`, `font-headline` for headings, orange
gradient instead of indigo/slate for the highlight panel). Left `AnomalyTable`'s internal
table row styling (`bg-gray-50` header/hover) alone — neutral utility classes, not a real
contributor to the style mismatch, not worth the churn.

**A second real bug surfaced while restyling and was fixed, not left in place**: the
"Vendor Collusion Graph Active" panel showed "0 active projects... 0 works flagged... 0
critical anomalies" even with a successful health check. Root cause: the `/api/anomalies/
summary` proxy route wraps the backend payload as `{success, data: {...}}`, but the page
read fields directly off the top-level response (`d.total_works`) instead of `d.data.
total_works` — every field silently defaulted to 0 via `??`. Fixed by unwrapping `.data`
correctly.

**Browser-verified**: page now visually matches the rest of the app (orange header card,
orange gradient panel), and the Vendor Collusion panel correctly shows "98,003 active
projects... 4,901 works flagged... 1,268 critical anomalies" — real numbers, matching the
live backend exactly.

## 8. Silent-failure secondary data

### Problem
`/overview/state/[id]`'s MP-performance fetch and `/mps/[name]`'s "All Works" fetch both had
no error state at all — on failure, the section just silently disappeared or showed ₹0
totals, indistinguishable from "this state/MP genuinely has no data." (`/ml-dashboard`'s
summary silent-failure was already fixed as part of item #5/6's envelope-unwrap bug.)

### Status: Done (2026-09-12)

Added `mpsError` state to `/overview/state/[id]` and `allWorksError` state to
`/mps/[name]`, both set on non-ok response or thrown exception (distinct from a
legitimately-empty successful response) and rendered as a visible amber notice explaining
the numbers shown may be incomplete.

**Browser-verified no false positives**: loaded a real MP page with genuinely empty
completed-works data — no error banner appeared (correctly distinguishing "empty result"
from "fetch failure"), confirming the fix doesn't cry wolf on legitimate empty states.

## 9. Responsive grid fallbacks

### Problem
`/overview` (2 spots), `/states` (1 spot), `/projects/[id]` (1 spot) used `grid-cols-2` as
the base (no smaller mobile fallback), risking a cramped 2-column squeeze under ~400px.

### Status: Done (2026-09-12)

Changed all 4 to `grid-cols-1 sm:grid-cols-2 ...` so they stack to a single column below
the `sm` breakpoint. Caught and avoided a mistake mid-fix: initially reached for an
`xs:grid-cols-2` variant on `/projects/[id]`, but this theme defines no custom `xs`
breakpoint — that would have been a silently-dead, no-op class. Used `sm:`/`lg:` instead.

**Browser-verified at 390px width** (a common small-phone size): `/overview`'s KPI cards
and `/states`' overview strip both now stack cleanly to one column instead of squeezing two
narrow cards side by side.

## 10. Minor cleanup

### Status: Done (2026-09-12)

Removed the unused `ida_agency` field from `RawCompletedRecord` in both `/mps/[name]` and
`/overview/state/[id]` — declared in the TS interface but never rendered anywhere.
Color-only status badges (reviewed during the original audit) were found to already always
pair color with a text label everywhere in the app — no changes needed there; the original
audit note was a "worth double-checking" flag, not a confirmed defect.

---

## Summary

All 10 tracked items are now done, each browser-verified (not just code-inspected) where a
live check was meaningful. Along the way, fixing these surfaced and fixed several
**additional real bugs** beyond the original audit's scope:
- The `/ml-dashboard` summary fetch was silently reading fields off the wrong object level
  (`d.total_works` instead of `d.data.total_works`), so real data existed but every number
  shown was a silently-wrong zero.
- The `/anomalies` "Model Accuracy 93.8%" / "ROC-AUC 0.8972" turned out to be entirely
  fabricated with no backing API field at all, and conceptually invalid for an unsupervised
  IsolationForest with no ground-truth labels to score against in the first place.
- The landing page's fake "875 Cr" fallback had a duplicate, independent fake-default layer
  inside `StatStrip` itself (2715/37/124/11) that would have silently reactivated if a
  future caller ever omitted a prop.
- A stale fake fallback ("860" critical anomalies) had drifted from the real current value
  (1,268) — proof that hardcoded placeholders rot silently over time even when originally
  chosen to look plausible.

Remaining known gaps **not** covered by this tracker (out of scope for a UI-polish pass,
noted for future work): the `backend/backend_api.py` historical-CSV dataset still can't be
scoped by district/MP-name for RBAC (Epic 1's documented gap), and Epic 6's live LLM call
path remains untested without a real `ANTHROPIC_API_KEY`.
