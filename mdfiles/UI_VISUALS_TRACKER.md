# UI Responsiveness & Visuals Tracker

Living tracker for the responsiveness + visual-coverage audit. Update status inline as each item ships.

## Responsiveness

| # | Item | File | Status |
|---|---|---|---|
| R1 | No mobile nav — links `hidden` below `md`, no hamburger fallback | `frontend/src/components/Navbar.tsx:128` | DONE — added hamburger + slide-down mobile menu, closes on route change |
| R2 | `grid-cols-2` with no responsive variant, cramped on narrow phones | `frontend/src/app/compliance/page.tsx:988` | DONE — `grid-cols-1 sm:grid-cols-2` |
| R3 | Modals don't cap height/scroll on short mobile viewports | `frontend/src/components/features/WorkFeatureDetailModal.tsx`, `FeatureCatalogModal.tsx` | DONE — added `flex-1 min-h-0` to scrollable body so `overflow-y-auto` actually bounds correctly |

## Visuals

| # | Item | File | Status |
|---|---|---|---|
| V1 | `/overview/state/[id]` MP performance is fake CSS-width bars, not a real chart | `frontend/src/components/features/MPPerformanceSection.tsx` | DONE — added `MPPerformanceBarChart` (recharts), top-10 by active metric, ranked list kept below for full detail |
| V2 | `/overview/state/[id]` has no financial trend chart despite reusable components existing | `frontend/src/app/overview/state/[id]/page.tsx` | DONE — reused `OverviewFinancial` (recharts) with real allocated/sanctioned/expenditure from `StateSummary` |
| V3 | `/mps/[name]` individual MP page has zero charts | `frontend/src/app/mps/[name]/page.tsx` | DONE — added `StatusDonut` (recharts) computed from real lifecycle_status counts |
| V4 | `/admin/users` has zero visuals, not even a stat strip | `frontend/src/app/admin/users/page.tsx` | DONE — added active/invited/disabled/total stat cards |
| V5 | `/states` lists states as cards/table only; India map / StateHeatBar exist but unused here | `frontend/src/app/states/page.tsx` | DONE — added new `StateComparisonBar` (recharts), top-10 and bottom-10 by completion rate |

## Bugs found during this pass (not in original audit)

- **Risk alerts / Compliance Findings were always empty.** `seed_sample_data()` ran the compliance engine and logged results, but never called `raise_alerts_for_work`/`raise_findings_for_work` — so the Alert bell had zero rows on any fresh DB, independent of frontend correctness. Fixed in `db.py` + added `backfill_alerts_for_existing_works()` so already-deployed DBs self-heal on next restart. Added a 5th seed work with a genuine out-of-jurisdiction violation so there's a real alert to see out of the box. DONE.
- **India map showed 100% hardcoded numbers labeled "Live API Data".** `MOCK_CONSTITUENCIES` supplied every figure (sanctioned/utilized/works) on the landing-page map. Fixed by fetching `/api/v1/overview/states` and merging real aggregates in; mock data now only supplies lat/lng geography. DONE.
- **Compliance dashboard had two hardcoded fallback datasets.** `defaultRecentProjects` (5 fabricated project rows with fake future dates) and `fyDefaults` (a plausible-looking fake per-financial-year totals table) both silently stood in for real data while loading/on backend failure. Both removed in favor of honest zero/empty states. DONE.

## Notes
- India map component: `frontend/src/components/ui/india-map.tsx` (currently only used on landing page `/`).
- Reusable chart components in the codebase: `StatusDonut`, `OverviewFinancial`, `FinancialBars`, `RiskGauge`, `StateHeatBar`, `MPPerformanceBarChart` (new), `StateComparisonBar` (new) — all recharts-based.
- Verified via `tsc --noEmit` after every change and a full `npm run build` at the end; all pages compiled and built clean.

All items DONE as of this pass.
