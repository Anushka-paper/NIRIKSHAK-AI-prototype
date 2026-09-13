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
| V2 | `/overview/state/[id]` has no financial trend chart despite reusable components existing | `frontend/src/app/overview/state/[id]/page.tsx` | PENDING |
| V3 | `/mps/[name]` individual MP page has zero charts | `frontend/src/app/mps/[name]/page.tsx` | PENDING |
| V4 | `/admin/users` has zero visuals, not even a stat strip | `frontend/src/app/admin/users/page.tsx` | PENDING |
| V5 | `/states` lists states as cards/table only; India map / StateHeatBar exist but unused here | `frontend/src/app/states/page.tsx` | PENDING |

## Bugs found during this pass (not in original audit)

- **Risk alerts / Compliance Findings were always empty.** `seed_sample_data()` ran the compliance engine and logged results, but never called `raise_alerts_for_work`/`raise_findings_for_work` — so the Alert bell had zero rows on any fresh DB, independent of frontend correctness. Fixed in `db.py` + added `backfill_alerts_for_existing_works()` so already-deployed DBs self-heal on next restart. Added a 5th seed work with a genuine out-of-jurisdiction violation so there's a real alert to see out of the box. DONE.

## Notes
- India map component: `frontend/src/components/ui/india-map.tsx` (currently only used on landing page `/`).
- Reusable chart components already in the codebase: `StatusDonut`, `OverviewFinancial`, `FinancialBars`, `RiskGauge`, `StateHeatBar` (recharts-based).
- Verified via headless browser after each change, not just type-checking.
