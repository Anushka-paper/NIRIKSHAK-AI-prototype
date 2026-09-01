# MPLADS AI/ML Monitoring Platform — Complete Technical Implementation Blueprint

*Prepared from the Rajya Sabha MPLADS AI/ML Dataset Report and the Detailed Lok Sabha MPLADS AI/ML Dataset Analysis Report. This document is a practical build-and-present guide for a Smart India Hackathon (SIH) submission: it maps every dataset field to a concrete engineering step, states plainly where a claim requires data you don't yet have, and never asserts that an anomaly is proof of fraud.*

---

## 1. Executive Summary

MPLADS (Members of Parliament Local Area Development Scheme) generates six linked but separately-filed datasets: **MP Allocation**, **Works Recommended**, **Works Sanctioned**, **Expenditure on Completed & Ongoing Works**, **Works Completed**, and **Amount Consented for Calamity**. Individually each is a static table. Joined on **Work ID**, **MP**, **constituency**, **state**, **IDA (Implementing/District Authority)**, and **date/amount fields**, they become a single work-level lifecycle graph:

```
Allocation → Recommendation → Sanction → Expenditure (N transactions) → Completion
                                              ↘
                                        Calamity Consent (parallel track)
```

The platform you are building is **not** a single ML model. It is a **layered decision-support system**:

| Layer | Answers | Example |
|---|---|---|
| Rule engine | "Is this a known, defined violation?" | Expenditure recorded before sanction date |
| Statistics | "Is this far from the historical/peer normal?" | Transaction amount above the 95th percentile for its category |
| Unsupervised ML | "Is this an unusual combination of many features at once?" | Isolation Forest flags a transaction with an odd amount+timing+vendor combination |
| NLP | "Does this look like something we've already funded?" | Two work descriptions have 92% cosine similarity |
| Predictive ML | "Is this likely to become a problem?" | A work's spending pattern resembles historically-delayed works |
| Risk fusion | "Given everything, how urgently should a human look at this?" | Composite risk score = 87/100, Critical |

Every output is a **prioritised, explainable signal for human review** — never an automatic finding of fraud or misconduct. This distinction is stated explicitly in both source reports and must be preserved throughout the build and the SIH pitch.

The six **sample** CSVs (9–13 rows each) exist only to prove the data model and pipeline design. Statistical thresholds, ML baselines, and predictive models must be *trained/calibrated on the production dataset* (expected to hold thousands of records) — the sample size is analytically too small to establish a "normal" distribution, and this document says so wherever a technique depends on volume.

---

## 2. Understanding the MPLADS Data Lifecycle

Every MPLADS work moves through a predictable sequence of *states*, and each state is recorded in a different CSV:

1. **Allocation** — each MP is given a financial ceiling (the Allocated Limit dataset) for a period. This is the denominator for every utilisation calculation.
2. **Recommendation** — the MP recommends a work (Works Recommended dataset) with an estimated cost, description, category, and location.
3. **Sanction** — the implementing authority approves the work (Works Sanctioned dataset), fixing an approved cost and start of the compliance checkpoint.
4. **Expenditure** — money is actually disbursed against the sanctioned work, potentially across many transactions, to vendors, over time (Expenditure dataset). This is the only genuinely *transactional* (many-rows-per-work) dataset.
5. **Completion** — the work is finished and evidenced (Works Completed dataset), closing the lifecycle.
6. **Calamity Consent** — a parallel, non-standard-works track for emergency/disaster funding (Amount Consented for Calamity dataset), which has its own rules and should not be forced into the same benchmarks as ordinary works.

The reason this matters for the AI/ML design: **most interesting signals live in the transitions between states**, not in any single table. A sanctioned amount alone tells you nothing suspicious; a sanctioned amount that is 40% above the recommended amount, sanctioned in one day, for a vendor who received three same-day payments of an identical amount elsewhere — that is a cross-dataset pattern, and it is only visible once the tables are joined.

---

## 3. Complete Dataset Architecture & Joins

| Dataset | Grain (1 row =) | Primary key(s) | Joins to |
|---|---|---|---|
| Allocated Limit for MPs | one MP's allocation ceiling for a period | MP + (Constituency/State) | Recommendation, Sanction, Expenditure via MP |
| Works Recommended | one proposed work | Work ID | Sanctioned (Work ID), Completed (Work ID, weak) |
| Works Sanctioned | one approved work | Work ID | Recommended (Work ID), Expenditure (Work ID), Completed (Work ID) |
| Expenditure on Completed & Ongoing Works | one transaction against a work | Work ID + Date + Vendor (composite; no natural transaction ID observed) | Sanctioned (Work ID) |
| Works Completed | one finished work | Work ID | Sanctioned (Work ID), Expenditure (Work ID) |
| Amount Consented for Calamity | one calamity consent event | MP + Calamity/Date (no Work ID observed) | MP only — this table does **not** reliably link to Work ID in the supplied samples |

**Available in current dataset:** Work ID as the join key across Recommended → Sanctioned → Expenditure → Completed; MP/constituency/state as the join key for Allocation.
**Requires additional data:** a reliable Work ID (or equivalent) linking Calamity Consent to downstream works/expenditure. The source report explicitly notes this linkage is only "partial" — do not build a demo that claims calamity funds are traced to specific expenditure unless you add this key.

### Entity Resolution — what happens when keys don't match cleanly

| Problem observed/likely | Strategy |
|---|---|
| Work ID missing in a row | Route to a "needs manual linkage" queue; do not silently drop the row — a missing Work ID is itself a data-quality/compliance signal (see §6, §13). |
| Work ID formatted differently (e.g., the Recommended/Sanctioned raw CSVs bundle Work ID with a long category description and inconsistent tabs/spacing — noted explicitly in the Lok Sabha report) | Write a deterministic parser (regex split on the first numeric/alnum token pattern observed in the sample) that extracts a canonical `work_id` and stores the untouched original string as `work_id_raw` for audit. |
| MP name spelled differently across files ("Shri X", "Mr. X", trailing whitespace) | Normalise: strip honorifics/titles, trim whitespace, lowercase for matching, keep the original for display. Maintain an `mp_master` table with a stable `mp_id`, and a `mp_alias` table mapping every observed spelling to `mp_id`. |
| Vendor names differ (abbreviations, Pvt Ltd vs Private Limited, case) | Same alias-table approach as MP names; additionally apply fuzzy matching (token-sort ratio) and route matches between 80–95% similarity to a human-confirmation queue rather than auto-merging. |
| Dates in different formats or clearly invalid (sanction before recommendation) | Parse to ISO-8601 with a strict parser; flag unparseable or logically-impossible sequences as data-quality violations (this becomes a rule in §13), not silently corrected. |

This entity-resolution layer is what makes every downstream feature ("Sanction Delay Days", "Vendor Concentration", etc.) trustworthy — skipping it produces features computed on the wrong join and silently wrong risk scores.

---

## 4. Dataset-by-Dataset Analysis (Purpose, Fields, Problems Solved, Features)

For each dataset: **A. Purpose → B. Field-by-field → C. Problems it solves → D. Features to engineer.**

### 4.1 Allocated Limit for Hon'ble MPs

**A. Purpose.** The financial ceiling against which every other rupee spent must eventually be interpreted. Sample: 9 records, combined allocation ≈ ₹1,439,038,565.

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| MP | identity of the allocation holder | text (needs `mp_id` resolution) | spelling variants, honorifics | join key for every utilisation calc |
| Constituency / State | geography | text | inconsistent naming | peer-group key for benchmarking |
| Allocated Amount | ceiling in ₹ | numeric (currency-formatted) | commas/symbols, blank | denominator for utilisation % |
| (Period/Financial Year, if present in production) | scope of the ceiling | date/text | must exist for multi-year data | required to avoid comparing utilisation across incompatible years |

**C. Problems solved.** Fund-utilisation baseline; allocation-limit compliance; MP-to-MP and state-to-state comparison; identifying "low-output, high-resource" patterns once joined to recommended/sanctioned/completed counts.

**D. Features.**
- `utilisation_pct = total_expenditure / allocated_amount × 100`
- `remaining_allocation = allocated_amount − relevant_sanctioned_or_spent_amount`
- `utilisation_rate_of_change` (period-over-period, once multi-period data exists)
- `peer_percentile_utilisation` (this MP's utilisation vs. all MPs in the same state/period)
- `output_per_rupee = count(completed works) / allocated_amount`

*Available now:* allocation amount, MP/geography. *Derived:* utilisation %, remaining balance. *Requires additional data:* explicit financial-year field to make multi-year trend and utilisation comparisons valid — without it, don't compute a "utilisation over time" chart, only a point-in-time snapshot.

---

### 4.2 Works Recommended

**A. Purpose.** The planning/estimate baseline — the earliest point a work exists on paper. Sample: 11 works, combined recommended amount ≈ ₹4,277,772.

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| Work ID | lifecycle key | text/alphanumeric | bundled with category text + tab inconsistencies in the raw CSV (confirmed in the report) | primary join key — must be parsed before anything else |
| MP / Constituency / State / IDA | who proposed it, where | text | naming variants | grouping key for trend & peer analysis |
| Work Description | free text | text | verbosity, boilerplate, spelling | input to NLP duplicate detection (§8) |
| Category | work type (road, sanitation, etc.) | categorical | inconsistent category labels across years | benchmarking group for cost/duration norms |
| Recommendation Date | when proposed | date | format inconsistency | start of the delay-measurement chain |
| Recommended Amount | initial cost estimate | numeric | currency formatting | baseline for estimate-variance calculations |

**C. Problems solved.** Recommendation-volume trend detection (by MP/state/category/month); duplicate/near-duplicate work detection at the earliest possible stage (cheapest point to catch it); recommendation-to-sanction delay measurement once joined to Sanctioned; unusually large or repeated recommended amounts.

**D. Features.**
- `recommendation_count_by_mp_month`, `recommendation_count_by_category_month` (volume trend inputs)
- `recommended_amount_zscore_within_category`
- `description_embedding_vector` (for §8 duplicate detection)
- `is_amount_repeated` (flag: this exact amount appears N+ times for this MP/category)
- `days_since_recommendation` (aging feature for works that never reach sanction)

---

### 4.3 Works Sanctioned

**A. Purpose.** The approval checkpoint and the financial figure that everything downstream (expenditure, overruns) is measured against. Sample: 11 records, combined sanction amount ≈ ₹4,529,591.

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| Work ID | join key | text | same parsing issue as Recommended | links to Recommended/Expenditure/Completed |
| Sanction Date | approval date | date | must be ≥ Recommendation Date | delay calculation; compliance rule input |
| Sanction Amount | approved cost | numeric | currency formatting | baseline for cost-overrun % |
| Status | workflow state (e.g. "Sanction", "Physical Inspection" — both observed in the sample) | categorical | inconsistent status vocabulary over time | status-aging feature; stuck-in-stage alerting |

**C. Problems solved.** Recommendation-to-sanction delay (`Sanction Date − Recommendation Date`); cost-estimate control (recommended vs sanctioned variance); compliance checkpoint (expenditure should not occur before sanction — enforced later against Expenditure); status-aging monitoring for works stuck mid-workflow.

**D. Features.**
- `sanction_delay_days = sanction_date − recommendation_date`
- `estimate_variance = sanction_amount − recommended_amount`
- `estimate_variance_pct = estimate_variance / recommended_amount × 100`
- `status_age_days = today − last_status_change_date`
- `sanction_delay_percentile_within_category_and_state` (peer-relative delay, not an arbitrary fixed threshold — see §11)

---

### 4.4 Expenditure on Completed and Ongoing Works

**A. Purpose.** The only true transaction-level table — this is where financial-anomaly and fraud-risk-indicator work is concentrated. Sample: 10 populated transactions, ≈ ₹245,636 total (blank trailing rows correctly excluded per the report).

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| Work ID | links to Sanctioned | text | same parsing caveat | join key for cost-overrun calc |
| Expenditure/Transaction Date | when paid | date | must be ≥ sanction date (rule) | spending-velocity and timing features |
| Vendor | who was paid | text | name variants, abbreviations | vendor-concentration and network features |
| Amount | transaction value | numeric | currency formatting | anomaly-score input |
| Payment Status | workflow state of the payment | categorical | inconsistent vocabulary | stuck-payment alerting |

**C. Problems solved.** Cumulative expenditure & utilisation tracking; spending-velocity/spike detection; cost-overrun detection (cumulative/final expenditure vs sanction); vendor concentration and relationship analysis; duplicate/suspicious-payment detection; the statistical/ML backbone of the whole fraud-risk-indicator layer (§7).

**D. Features.**
- `cumulative_expenditure_by_work`, `expenditure_to_sanction_pct = cumulative_expenditure / sanction_amount × 100`
- `transaction_amount_zscore_within_category`, `transaction_amount_percentile`
- `days_since_sanction_at_transaction` (spending velocity)
- `inter_transaction_gap_days` (rolling gap between consecutive transactions on the same work — inactivity signal)
- `vendor_concentration_pct = vendor_total_value / total_relevant_expenditure × 100`
- `vendor_transaction_count`, `vendor_work_count`, `vendor_constituency_count` (vendor profile — §7, §27)
- `same_day_same_vendor_txn_count` (the exact pattern the Lok Sabha report calls out: repeated ₹36,159 transactions, same vendor, same date, different Work IDs — flagged explicitly as *"a pattern requiring contextual analysis, not automatic fraud"*)
- `amount_repeat_count` (how many times this exact amount recurs for this vendor/work/MP)

---

### 4.5 Works Completed

**A. Purpose.** Physical closure of the lifecycle, with completion evidence. Sample: 9 records, ≈ ₹7,256,340 disbursed.

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| Work ID | join key | text | parsing caveat | links to Sanctioned/Expenditure |
| Work Description | text | text | boilerplate | duplicate-completed-work detection |
| Completion Date | finish date | date | must be ≥ sanction date | project-duration calculation |
| Amount (disbursed) | final amount | numeric | currency formatting | financial-physical reconciliation |
| Image/Evidence indicator | presence of completion proof | boolean/URL | frequently missing (observed in sample) | completeness/compliance feature today; input to future computer-vision similarity checks *if actual image files/URLs are supplied* |

**C. Problems solved.** Delayed-project detection (`Completion Date − Sanction Date` vs. peer benchmark); financial–physical reconciliation (does spending match completion status?); missing-evidence compliance signal; repeated/highly-similar completed-work detection.

**D. Features.**
- `project_duration_days = completion_date − sanction_date`
- `duration_percentile_within_category_state_size`
- `has_completion_evidence` (boolean) and `evidence_completeness_score`
- `financial_physical_mismatch_flag` (completed status but cumulative expenditure far below sanction, or vice versa)
- `disbursed_vs_sanctioned_variance_pct`

---

### 4.6 Amount Consented for Calamity

**A. Purpose.** A parallel emergency-fund monitoring track, structurally simpler and *not* subject to the same normal-works benchmarks. Sample: 13 records, ≈ ₹40,567,400 total consent.

**B. Fields.**

| Field | Meaning | Type | Data-quality risks | Analytical/ML use |
|---|---|---|---|---|
| Calamity (type/name) | disaster classification | categorical | free-text variants | grouping key for peer comparison |
| MP | who consented the fund | text | naming variants | MP-level aggregation |
| Consent Date | when approved | date | format inconsistency | timing/frequency features |
| Consent Amount | value | numeric | currency formatting | outlier detection input |

**C. Problems solved.** Calamity-wise/MP-wise trend and concentration; unusually large consent vs. comparable calamity events; consent-to-downstream-activity timing — **only if** a reliable link to a Work ID or expenditure record is added (currently absent, per §3).

**D. Features.**
- `consent_amount_zscore_within_calamity_type`
- `consent_frequency_by_mp_period`
- `consent_concentration_by_calamity_event`
- `days_since_consent_without_linked_activity` — *Requires additional data* (a Work ID/expenditure linkage) to compute reliably; do not fabricate this feature from the current schema.

---

## 5. Complete Data Pipeline (Raw CSV → Platform)

```
Raw CSV files (6 datasets)
   ↓  [Ingestion]      Load with schema detection; log row counts, encoding; quarantine unparseable rows
Data cleaning
   ↓  [Cleaning]       Strip blank/trailing rows (seen in Expenditure sample); trim whitespace; fix encoding
Data validation
   ↓  [Validation]     Type checks, null profiling, date-sequence checks, currency parsing, referential checks
Data standardisation
   ↓  [Standardise]    Canonical date format, canonical currency (numeric ₹), canonical category vocabulary
Entity resolution
   ↓  [Resolve]        Parse composite Work ID field; build MP/vendor/IDA alias tables; assign stable IDs
Dataset integration
   ↓  [Integrate]      Join on Work ID / MP+period / MP; build the unified work-lifecycle table
Feature engineering
   ↓  [Features]       Compute all features listed in §4 and §7 (financial, temporal, textual, relational)
Rule-based compliance engine
   ↓  [Rules]          Deterministic checks (§13) run on every new/changed record
Statistical analysis
   ↓  [Stats]          Percentiles, z-scores, IQR, rolling averages per peer group (§10)
ML anomaly detection
   ↓  [ML]             Isolation Forest / LOF on multivariate feature vectors (§6)
NLP analysis
   ↓  [NLP]            Embeddings + cosine similarity for duplicate-work detection (§8)
Predictive models
   ↓  [Predict]        Delay-risk / cost-risk models once enough historical outcomes exist (§21)
Risk scoring
   ↓  [Fuse]           Weighted combination of rule/stat/ML/NLP/predictive signals into one explainable score (§15)
Early-warning system
   ↓  [Warn]           Threshold crossing → alert object with evidence, generated and stored (§14)
Dashboard
   ↓  [Present]        Executive / MP / Work-360 / Vendor / Compliance / Early-Warning views (§24)
Human/auditor investigation
   ↓  [Review]          Analyst marks alert as valid / dismissed / data-quality issue / under investigation
                          → outcome feeds back into model calibration (§21)
```

Every arrow above is a **table-to-table or job-to-job data contract** you should document explicitly in your SIH slides (input schema → output schema), because judges will ask "what exactly moves between these boxes."

---

## 6. Trend Detection — What "Trends" Means Here

A **trend** is a *persistent or meaningful change over time or across a defined group* — a single unusual row is an **anomaly** (§7), not a trend. Keep this distinction sharp; conflating them is the most common weak point in similar hackathon pitches.

### 6.1 Financial trends
- **Increasing/decreasing expenditure:** aggregate `Amount` by month/quarter/FY, per MP/state/category; fit a rolling average and a linear slope; a persistently positive/negative slope over ≥3 periods = trend.
- **Sudden spending spikes:** a single period's total is a large z-score outlier vs. its own rolling mean — this is an anomaly *within* a trend series, flagged separately from the slope.
- **Unusual spending concentration:** Gini coefficient or top-N-share of expenditure by vendor/constituency/category, tracked over time.
- **Increasing/decreasing average project cost:** rolling mean of `Sanction Amount` per category per period.
- **Recurring/end-period spending patterns:** group by (day-of-month / quarter-end proximity) and compare volume against the rest of the period — classic "use-it-or-lose-it" fiscal-year-end spending signature.

*Required fields:* Date, Amount, MP/State/Category. *Aggregation:* group-by + time bucket. *Statistical technique:* rolling mean/median, linear slope, Mann-Kendall trend test for robustness on sparse series. *ML technique (optional, larger data):* change-point detection (e.g., PELT algorithm). *Visualisation:* time-series line chart with a shaded rolling band. *Alert condition:* slope statistically different from zero over a minimum window, or a period value beyond peer variance. *Example:* if a constituency's monthly expenditure grows from ₹2L → ₹3L → ₹4.5L over three consecutive months while peers stay flat, that is a trend worth a dashboard callout, not by itself an anomaly alert.

### 6.2 Operational trends
- **Sanction delays trending up/down:** rolling median of `sanction_delay_days` by month/category.
- **Increasing pending/ongoing works:** count of works in "not yet completed" status per period.
- **Decreasing completion rates:** `completed_count / sanctioned_count` per period, rolling.
- **Changes in project duration:** rolling median of `project_duration_days` by category.

### 6.3 Geographical trends
- State/constituency-level concentration of recommended/sanctioned value (share of national total over time).
- Category-wise geographic clustering (e.g., a disproportionate share of "road works" recommended in one state vs. national category mix).

### 6.4 Vendor trends
- Vendor concentration increasing over time (`vendor_concentration_pct` rolling).
- A vendor receiving unusually large cumulative amounts vs. the vendor population distribution.
- The same vendor repeatedly serving the same constituency (`vendor_constituency_repeat_count`) — a relational trend, feeds the network-analysis layer (§16).

### 6.5 Work-category trends
- Volume, value, average delay, and average risk score, tracked per category (roads, community infrastructure, education, health, sanitation, other) over time — this becomes one filterable dimension on almost every dashboard view in §24.

**Important caveat:** on the 9–13-row samples, none of the above trend calculations are statistically meaningful — they exist to prove the *pipeline*, not to report a real trend. State this explicitly when demoing.

---

## 7. Fund Utilisation Monitoring

```
Allocation → Recommended → Sanctioned → Expenditure → Completed
```

**Core formula:** `Utilisation % = Expenditure / Allocation × 100` (per the Rajya Sabha report's own formula). Also track sanction-stage utilisation (`Sanctioned / Allocation × 100`) as an earlier-warning proxy before money actually moves.

| Pattern | How detected | Why it matters |
|---|---|---|
| Under-utilisation | `utilisation_pct` far below peer median for the same period | Possible planning/execution bottleneck |
| Rapid/unusually high utilisation | `utilisation_pct` growth rate far above peer median, or utilisation approaching/exceeding 100% early in the period | Possible end-loading, or an allocation-limit compliance issue |
| Unused allocation | `remaining_allocation` still near the full ceiling close to period end | Efficiency concern, not misuse |
| Constituency/MP/state comparison | percentile rank of `utilisation_pct` within peer group | Surfaces relative outliers without needing an absolute "correct" number |
| Historical/year-wise comparison | year-over-year change in utilisation for the same MP/constituency | Distinguishes a one-off dip from a persistent pattern |

These become: **dashboard metrics** (single utilisation % gauge per MP/constituency), **trend inputs** (§6.1), **anomaly features** (fed into the Isolation Forest feature vector in §8), and **early-warning signals** (a sudden utilisation spike close to fiscal year-end, combined with other risk indicators, raises the composite risk score in §15).

---

## 8. Expenditure Anomaly Detection — Full Process

**Step 1 — Transaction-level features.** Build the row-level feature vector per transaction: `amount`, `amount_zscore_within_category`, `days_since_sanction`, `inter_transaction_gap_days`, `vendor_concentration_pct`, `same_day_same_vendor_txn_count`, `payment_status`, `expenditure_to_sanction_pct_after_this_txn`.

**Step 2 — Historical baselines.** For every peer group (category × state, category × project-size bucket, vendor), compute mean, median, standard deviation, and IQR of transaction amount and timing, refreshed periodically as new data arrives.

**Step 3 — Compare against multiple reference frames**, not just one: same work category, same constituency, same state, same vendor, similarly-sized projects, and the work's own historical behaviour (has *this* work's spending pattern shifted?).

**Step 4 — Statistical methods.**
- **Mean/median/SD:** basic central tendency and spread per peer group.
- **IQR:** `Q3 + 1.5×IQR` / `Q1 − 1.5×IQR` as a robust-to-skew outlier fence (currency data is typically right-skewed, so prefer IQR/median over mean/SD alone).
- **Percentile:** rank a transaction's amount against its peer group; flag ≥95th or ≤5th percentile as attention-worthy, not automatically "anomalous."
- **Z-score:** `(x − mean) / SD` — useful once a peer group is large enough (≥30 observations) for the normal approximation to be reasonable; the current samples are far too small.
- **Rolling averages:** per-work or per-vendor rolling mean/median to catch a *shift* in behaviour rather than a single outlier point.

**Step 5 — Unsupervised ML.**
- **Isolation Forest:** input = the multivariate feature vector from Step 1 (numeric, scaled); it isolates points that are easy to separate from the rest of the data via random splits — points requiring fewer splits get a higher anomaly score. Good for high-dimensional, label-free data; interpretation requires pairing the score with the top contributing features (e.g., SHAP or simple feature-deviation ranking) so the alert is explainable (§17), not a bare number. Limitation: sensitive to feature scaling and to contamination-rate assumptions; needs periodic retraining as "normal" shifts.
- **Local Outlier Factor (LOF):** compares a point's local density to its neighbours' density — better than Isolation Forest at catching anomalies that are only unusual *relative to a nearby cluster* (e.g., a transaction that's normal nationally but unusual for its specific category/state cluster). Limitation: computationally heavier at scale; needs a well-chosen `k` (neighbourhood size).
- **DBSCAN/clustering:** groups transactions into density-based clusters; points that don't fall into any cluster ("noise" points) are candidate anomalies. Useful for discovering *natural* peer groups (e.g., "small road works under ₹50k" as an emergent cluster) rather than only using pre-defined categories.

**Step 6 — Anomaly score.** Combine the statistical percentile/z-score and the ML model's score (e.g., min-max normalise each to 0–100 and average, or take the max) into a single `expenditure_anomaly_score` per transaction, which becomes one input to the overall risk score in §15 — it is never presented alone as "this is fraud."

---

## 9. Potential Misuse / Fraud-Risk Indicators

**Framing (repeated deliberately, because it matters for both engineering and the SIH pitch):** the platform identifies **risk indicators that warrant human review**, never a finding of fraud. An anomaly is a statistical fact; fraud is a legal conclusion that requires investigation and corroborating evidence outside this dataset.

| Indicator | Dataset(s) | Columns used | Feature | Detection logic | Algorithm | Risk level guide | Recommended human action |
|---|---|---|---|---|---|---|---|
| Expenditure above sanctioned amount | Expenditure + Sanctioned | Amount, Sanction Amount | `expenditure_to_sanction_pct` | flag if cumulative > 100% (subject to valid revised-sanction records) | Rule | High | Check for a valid revised sanction before escalating |
| Expenditure before sanction | Expenditure + Sanctioned | dates | `days_since_sanction` negative | flag if txn date < sanction date | Rule | Critical | Immediate compliance review |
| Unusually large/small transaction | Expenditure | Amount | `amount_zscore`, `amount_percentile` | beyond peer-group threshold | Statistics / IF / LOF | Medium–High | Compare against category norms before flagging |
| Sudden spending spike | Expenditure | Date, Amount | rolling-window sum vs. history | change-point/rolling z-score | Statistics | Medium | Check for a legitimate large one-off procurement |
| Duplicate-looking payments | Expenditure | Work ID, Vendor, Amount, Date | `amount_repeat_count`, `same_day_same_vendor_txn_count` | repeated key combination | Rule + statistical review | Medium (never auto-High) | Contextual check — legitimate instalments look similar (§10) |
| Repeated vendor relationships | Expenditure | Vendor, Work ID, Constituency | `vendor_work_count`, `vendor_constituency_repeat_count` | high repeat count vs. peer vendors | Statistics / graph | Medium | Review vendor selection process, not the vendor itself |
| Abnormal vendor concentration | Expenditure | Vendor, Amount | `vendor_concentration_pct` | vendor share far above peer distribution | Statistics | Medium–High | Procurement-policy review |
| Unusual work-description similarity | Recommended/Sanctioned/Completed | Work Description | `description_similarity_score` | cosine similarity above threshold + matching context | NLP (§10 below) | Medium | Auditor confirms duplicate vs. legitimately similar work |
| Financial/physical mismatch | Expenditure + Completed | Amount, Status, Completion Date | `financial_physical_mismatch_flag` | high spend with no completion record, or completed with unresolved financials | Rule + Statistics | High | Site/physical verification |
| Unusually long project duration | Sanctioned + Completed | dates | `duration_percentile` | above peer 90th/95th percentile | Statistics | Medium | Check for legitimate scope changes |
| Missing completion evidence | Completed | Image/evidence field | `has_completion_evidence` | boolean false | Rule | Low–Medium (data-quality signal first) | Request evidence before elevating risk |
| Unusual payment timing | Expenditure | Date | fiscal-year-end clustering, off-hours/weekend timestamps if available | Statistics | Low–Medium | Contextual — many legitimate payments cluster near year-end |
| Repeated amounts | Expenditure | Amount | `amount_repeat_count` across unrelated works/vendors | Statistics | Low–Medium | Could be a standard rate card, not misuse |
| Suspicious clustering of multiple signals | All | composite | multiple indicators co-occurring on the same work/vendor/MP | Risk fusion (§15) | High–Critical | Priority investigation queue |

**Design principle from both reports:** *multiple independent signals converging on the same work/vendor/authority should raise priority faster than any single strong signal alone* — this is why §15 uses a weighted sum rather than a single max().

---

## 10. Duplicate Work Detection

```
Work Description
   ↓  Text cleaning (lowercase, strip punctuation/boilerplate, expand common abbreviations)
   ↓  Sentence embeddings (e.g., a Sentence-Transformers model such as all-MiniLM-L6-v2, or multilingual variant for Hindi/regional text)
   ↓  Vector representation (384–768-dim dense vector per description)
   ↓  Cosine similarity (pairwise or via approximate-nearest-neighbour index at scale — see §28)
   ↓  Similarity threshold (e.g., ≥0.85 "high similarity" candidate — calibrate on production data, don't hardcode blindly)
   ↓  Potential duplicate → contextual filter → human review
```

**Level 1 — Exact matching:** Work ID equality (catches accidental re-ingestion), and exact-string description + amount + MP + constituency match (catches copy-pasted records).

**Level 2 — Fuzzy matching:** token-sort/token-set ratio (e.g., Levenshtein-based) catches near-identical text with typos, reordering, or minor edits — cheaper than embeddings and a good first filter before running the NLP step on the full corpus.

**Level 3 — NLP semantic similarity** (the pipeline above): catches works described differently but meaning the same thing (e.g., "Construction of concrete road from X to Y" vs. "CC road development, X-Y stretch").

**Reducing false positives:** two works about "construction of a community hall" in different states are not duplicates. Require semantic similarity **AND** matching on location (constituency/state), category, comparable amount (within a tolerance band), and proximate dates before elevating to a duplicate candidate — this is the same "contextual attribute" gate specified in the Lok Sabha report (Stage 6: "increase confidence only when semantic similarity is accompanied by matching contextual attributes").

**Worked example:** Work A — "Construction of cement concrete road in Ward 4, ₹3,50,000, recommended 12-Jan"; Work B — "CC road work Ward 4 area, ₹3,45,000, recommended 15-Jan." Description cosine similarity = 0.91 (high); same constituency; amount difference 1.4% (within tolerance); dates 3 days apart. → **High-confidence duplicate candidate**, routed to an auditor with both records and the similarity/context breakdown shown side by side — the system does not merge or reject either record automatically.

## 11. Duplicate Payment Detection

Compare Work ID, Vendor, Amount, Date, MP, Constituency, and Payment Status across transactions.

- **Exact duplicates:** identical Work ID + Vendor + Amount + Date — very likely a data-entry/ingestion duplicate; safe to auto-flag for de-duplication review.
- **Near duplicates:** same Work ID + Vendor + Amount but a date within a few days — could be a resubmission or could be a legitimate second instalment.
- **Repeated payments:** the same amount recurring for a vendor across *different* Work IDs — the Lok Sabha report's own sample shows this exact pattern (repeated ₹36,159 transactions, same vendor/date/constituency, different Work IDs) and explicitly instructs treating it as **"a pattern requiring contextual analysis — not automatically as duplicate payment."**
- **Same amount patterns / same vendor-date patterns:** aggregate and rank by recurrence count, but do not assign risk purely from the count.

**Why a repeated payment is not automatically fraud, and what contextual validation looks like:** government payments are frequently **standardised** — a fixed day-labour rate, a standard material unit cost, or a recurring instalment schedule will legitimately produce identical amounts many times over. Contextual validation means checking: (a) are these payments against *different, genuinely distinct* sanctioned works (legitimate) vs. the *same* work paid twice (data issue)? (b) does the vendor's invoice/contract structure explain the repetition (e.g., a standard rate card)? (c) is the payment status workflow consistent (was each payment separately approved)? Only when the pattern **cannot** be explained by a standard rate/legitimate instalment structure, and coincides with other risk indicators, should it climb the risk score.

## 12. Delayed Project Detection

```
Recommendation Date → Sanction Date → Expenditure Date(s) → Completion Date
```

- **Recommendation-to-Sanction Delay** = `Sanction Date − Recommendation Date`
- **Sanction-to-Completion Duration** = `Completion Date − Sanction Date`
- **Expenditure inactivity gaps** = time between consecutive expenditure events on the same work

**How "delayed" is determined — not an arbitrary 30/60/90-day cutoff.** Establish norms *from the data itself*: compute the **median** and key **percentiles** (e.g., 75th, 90th) of each duration measure, segmented by **category** (a road work and a large community-hall project have structurally different normal durations), **state/IDA** (implementation capacity varies regionally), and **project-size bucket** (bucket sanctioned amount into small/medium/large tiers). A work is flagged as an outlier when its duration sits meaningfully above the 90th/95th percentile of its *own* peer group — not above one fixed number applied to every work nationwide.

- **Statistical detection:** percentile-rank flagging as above.
- **Anomaly detection:** feed `duration_percentile`, `inter_transaction_gap_days`, and `status_age_days` into the same Isolation Forest/LOF model used for financial anomalies, so a work that's unusual on *timing* surfaces alongside works unusual on *amount*.
- **Predictive delay models:** once enough historically-completed works with known durations exist, train a regression or survival/time-to-event model (features: category, state, sanctioned amount, sanction delay, early expenditure velocity) to estimate the *probability of on-time completion* for currently-ongoing works — enabling an early warning **before** the work is actually late.
- **Early warning before completion:** if an ongoing work's spending has stalled (`inter_transaction_gap_days` far above its category's norm) while it's still well before its predicted completion window, raise a "stagnation" alert rather than waiting for a hard deadline to pass.

**Worked example:** category "Community Infrastructure" has a median sanction-to-completion duration of 210 days (90th percentile = 320 days) once computed on production data. A specific work is at day 340 with no expenditure activity in the last 150 days. → Duration percentile > 95th, inactivity gap far above category norm → flagged as **delayed/at-risk**, with the peer-benchmark numbers shown alongside the alert for explainability.

## 13. Deviation from Established Norms

"Established norms" in this project = **statistically-derived, peer-group-specific expectations learned from historical data**, not fixed rules invented in advance (except where an explicit official rule exists, e.g., a legally mandated processing timeline).

Possible norms: normal project duration, normal project cost, normal expenditure frequency, normal vendor concentration, normal utilisation, normal sanction delay, normal category-level expenditure, normal transaction size.

```
Historical data
   ↓  Group comparable projects (by category × state/IDA × project-size bucket)
   ↓  Calculate baseline (median, IQR, or full distribution per group)
   ↓  Calculate expected range (e.g., IQR fences, or 10th–90th percentile band)
   ↓  Compare new/current project against its group's range
   ↓  Calculate deviation (percentile rank, or distance from median in IQR units)
   ↓  Risk score contribution (§15)
   ↓  Alert if deviation is large AND (ideally) corroborated by another signal
```

**Why norms should be dynamic, not fixed, wherever possible:** construction costs, typical project sizes, and processing capacity all drift over time and vary by region — a single hardcoded "₹5 lakh is normal for a road work" number will be wrong within a year and wrong across states immediately. Recompute baselines on a rolling schedule (e.g., quarterly) as new production data accumulates, and always version each baseline so an alert can show "flagged against the Q3-2026 baseline for Road Works in State X," making the comparison auditable and reproducible. Use fixed thresholds only where an *actual official rule* mandates a specific number (e.g., a legally defined maximum processing time) — clearly label those as rule-based, not statistical, in the explanation shown to the user.

## 14. Cost Overrun Detection

```
Recommended Amount → Sanction Amount → Actual Expenditure → Final Disbursed Amount
```

- **Estimate variance** = `Sanction − Recommended`
- **Estimate variance %** = `(Sanction − Recommended) / Recommended × 100`
- **Cost overrun** = `Actual/Final Expenditure − Sanction`
- **Cost overrun %** = `(Actual/Final Expenditure − Sanction) / Sanction × 100`

Use **cumulative expenditure** for ongoing works and **final/completion-stage disbursed amount** for completed works — comparing a completed work's *final* number against an ongoing work's *partial* number would understate overruns for works still in progress, so the two must be computed and labelled separately.

**Benchmarking:** always compare cost-overrun % against a **category-specific and project-size-specific** distribution (a 10% overrun might be entirely normal for a large multi-phase infrastructure work and unusual for a small single-vendor sanitation work).

**Distinguishing three tiers:**

| Tier | Definition | Action |
|---|---|---|
| Normal variation | overrun % within the category's typical IQR range | No alert; shown only in analytics |
| Significant deviation | overrun % beyond the 90th percentile for the category, but a single occurring signal | Medium-risk flag, contributes to §15 score |
| Potential cost-overrun risk | large deviation **combined with** another indicator (e.g., vendor concentration, missing evidence, unusual timing) | High/Critical, prioritised for review |

## 15. Financial vs. Physical Progress

This is the reconciliation step that links §14 (money) to §12 (completion): join Expenditure's `cumulative_expenditure` against Completed's `status`/`completion_date`. Two review-worthy mismatches: **(a) high cumulative expenditure with no completion record** — money is moving but the work is never marked done; **(b) a "completed" status with unresolved/very low recorded expenditure** — physical closure without a matching financial trail. Both are *reconciliation-failure signals*, not proof of anything on their own; they typically indicate either a data-entry gap or a genuine process issue, and only an auditor with access to physical site records can distinguish the two.

---

## 16. Automated Compliance Monitoring

| Compliance rule | Dataset | Fields | Logic | Alert | Severity |
|---|---|---|---|---|---|
| Expenditure without valid work | Expenditure + Sanctioned | Work ID | Work ID in Expenditure not found in Sanctioned | Unlinked expenditure | Critical |
| Expenditure before sanction | Expenditure + Sanctioned | dates | txn date < sanction date | Premature expenditure | Critical |
| Expenditure exceeding sanction | Expenditure + Sanctioned | Amount, Sanction Amount | cumulative > sanction (no valid revision) | Potential overspend | High |
| Missing sanction | Recommended + Sanctioned | Work ID | recommended work absent from Sanctioned beyond expected time | Unresolved recommendation | Medium |
| Excessive sanction delay | Recommended + Sanctioned | dates | delay beyond peer 90th/95th percentile (§13) | Processing delay | Medium |
| Missing completion record | Sanctioned + Completed | Work ID | sanctioned, well past expected duration, no completion row | Unresolved lifecycle | Medium |
| Delayed project | Sanctioned + Completed/Expenditure | dates | duration/inactivity beyond peer benchmark (§12) | Delayed/at-risk | Medium–High |
| Financial/physical mismatch | Expenditure + Completed | Amount, Status | high spend/no completion, or completed/low spend | Reconciliation failure | High |
| Suspicious repeated payments | Expenditure | Vendor, Amount, Date, Work ID | repeat pattern without contextual explanation (§11) | Payment-pattern review | Medium |
| Duplicate work candidate | Recommended/Sanctioned/Completed | Description, context | similarity ≥ threshold + matching context (§10) | Duplicate-work review | Medium |
| Unusual vendor concentration | Expenditure | Vendor, Amount | concentration % beyond peer distribution | Vendor-concentration flag | Medium |
| Missing evidence | Completed | Image/evidence field | evidence absent | Data-completeness flag | Low |
| Invalid dates | all | date fields | unparseable or logically impossible sequence | Data-quality issue | Low–Medium |
| Inconsistent amounts | all | amount fields | negative, zero, or implausible values | Data-quality issue | Low–Medium |
| Incomplete records | all | required fields | nulls in mandatory columns | Data-quality issue | Low |

**Execution flow, run automatically whenever new data arrives:**

```
Data arrives → Validation (schema/type/date checks) → Rules executed (table above)
   → Violations identified → Severity assigned → Risk score updated (§17)
   → Alert generated (only for medium+ severity, to avoid alert fatigue)
   → Dashboard updated → Human review → Reviewer outcome recorded → feeds calibration (§21)
```

This engine should run as an **incremental job**: on ingestion of new/changed rows, re-evaluate only the affected Work IDs/entities (not the entire dataset) so it scales to thousands of records without a full recompute each time.

---

## 17. Early-Warning System

**What triggers an early warning?** Any medium-or-higher severity compliance violation (§16), OR a composite risk score (§17 below) crossing the High/Critical threshold, OR a predictive model (§12, §21) indicating deteriorating completion probability *before* a hard deadline is missed.

**What data is required?** The unified work-lifecycle record plus all engineered features from §4/§7–§14.

**What features are calculated?** The full feature set — financial (utilisation, overrun%), temporal (delay/duration percentiles), relational (vendor concentration), textual (similarity score), and compliance (rule-violation flags).

**What model/rule is used?** A combination — the risk-fusion formula in §18, informed by rule outputs, statistical percentiles, ML anomaly scores, NLP similarity scores, and (where available) predictive-model outputs.

**How is severity determined?** By mapping the composite risk score to a band: 🟢 Low (0–39) / 🟡 Medium (40–64) / 🟠 High (65–84) / 🔴 Critical (85–100) — thresholds to be calibrated on production data, not fixed forever.

**When is the alert generated?** As soon as a record crosses into Medium or above, on the incremental job that re-evaluates changed records (not on a slow nightly batch alone — high-severity items should be near-real-time).

**Who sees the alert?** Routed to the relevant Compliance/Early-Warning dashboard view (§24) filtered by the reviewer's jurisdiction (state/IDA/MP), with Critical alerts additionally surfaced on the Executive Overview.

**What information does the alert contain?** Work ID and all linked source records; the composite score and the top contributing indicators (§19 explainability); the comparison baseline used for each indicator; timestamp; and rule/model version (so the same alert can be reproduced later, which matters for audit).

**Example alert object:**

```
Work ID: MPLADS-2026-004821
Risk Score: 87/100  →  🔴 Critical
Contributing indicators:
  • Cost deviation: expenditure 32% above sanctioned amount (peer 90th percentile: 14%)
  • Payment pattern: 3 same-day, same-vendor transactions of identical amount (context unresolved)
  • Vendor concentration: this vendor holds 61% of the constituency's total spend (peer median: 18%)
  • Duration: sanction-to-date elapsed time in the 97th percentile for its category
  • Financial/physical mismatch: no completion record despite 95% of sanctioned amount spent
Baseline version: Q3-2026 category/state benchmarks
Generated: 2026-09-01 08:14 IST
```

**What the auditor sees:** the alert above plus one click into the Work 360° view (§24) showing the full recommendation → sanction → every expenditure transaction → completion-evidence timeline, the specific peer-benchmark numbers each indicator was compared against, and buttons to mark the case Valid / Dismissed / Duplicate-of-another-alert / Data-quality issue / Escalate for investigation.

---

## 18. Risk-Scoring System

```
Risk Score = w1·Cost Risk + w2·Payment Risk + w3·Vendor Risk
           + w4·Delay Risk + w5·Duplicate Risk + w6·Compliance Risk + w7·Evidence Risk
```

**Feature normalisation:** convert every component to a comparable 0–100 scale before weighting — e.g., min-max scale a percentile-based feature directly (percentile *is already* 0–100), and min-max or logistic-squash a raw statistical score (z-score, IF anomaly score) so no single component dominates purely because of its native numeric range.

**Weighting:** start with **rule-based, hand-set weights** informed by domain judgement (e.g., a rule-engine "Critical" violation like expenditure-before-sanction should dominate the score almost by itself — set its weight/floor accordingly; softer statistical signals like a moderate cost-percentile deviation should contribute more modestly). Document the initial weights explicitly in your SIH deck as a starting hypothesis, not a claim of optimality.

**Score calculation:** weighted sum (or a weighted sum with an explicit floor for any Critical rule violation, so a single unambiguous violation can't be diluted by several mild statistical signals scoring low).

**Thresholds/severity:** 🟢 Low (0–39) · 🟡 Medium (40–64) · 🟠 High (65–84) · 🔴 Critical (85–100) — recalibrate the band edges using the distribution of scores actually observed on production data, so "High" reliably means "in the top slice of genuinely unusual cases," not an arbitrary fixed cut.

**Calibration over time:** once reviewers have marked enough alerts as Valid/Dismissed, treat those outcomes as **weak labels** and use a simple supervised model (e.g., logistic regression over the same component scores) to *learn* better weights than the initial hand-set ones — while keeping the rule-engine floor behaviour intact for the small number of unambiguous, legally-defined violations.

---

## 19. Why Multiple AI/ML Methods Are Required (Not One Model)

A single end-to-end ML model would need: (a) reliable fraud/non-fraud labels, which don't exist yet and are legally sensitive to assume; (b) a way to explain every decision to a public-finance auditor, which black-box models struggle with; (c) equal treatment of very different problem shapes (a known compliance rule, a statistical outlier, a text-similarity problem, and a time-to-event prediction are not the same kind of problem). Each layer therefore does the job it's actually good at:

- **Rule-based systems** — for *known, unambiguous* compliance violations (expenditure before sanction). Deterministic, instantly explainable, zero training data needed.
- **Statistical analysis** — for basic deviations and trends (percentiles, z-scores, IQR, rolling averages) where the "normal" comes directly from the historical distribution.
- **Unsupervised ML** (Isolation Forest, LOF, clustering) — for *multivariate* anomalies no single rule or single-variable statistic would catch, and where labelled fraud examples don't exist.
- **NLP** — the only practical tool for duplicate/similar-work detection given free-text descriptions with inconsistent wording.
- **Time-series analysis** — purpose-built for trend detection (§6), which single-row statistics cannot express.
- **Predictive ML** (XGBoost/LightGBM, survival models) — for forecasting delay/cost risk *before* it happens, once enough historical outcomes exist to learn from.
- **Computer vision** — *optional, future*, only if actual completion-evidence image files/URLs are supplied (not currently available in the sample schema) — would support image-similarity and repeated-evidence checks.
- **Graph/network analysis** — for MP–vendor–work relationship patterns (e.g., unusual vendor concentration across an MP's works) that a row-by-row model would never surface.

These layers **feed one another and converge** at the risk-fusion step (§18): rule outputs become one component of the composite score; statistical percentiles feed both the trend dashboards and the ML feature vectors; ML anomaly scores and NLP similarity scores are additional components; predictive-model outputs (where available) add a forward-looking component. No layer works in isolation from the final explainable output.

---

## 20. Comprehensive Feature-Engineering Table

| Feature | Formula/logic | Dataset(s) | Purpose | Model/use |
|---|---|---|---|---|
| Utilisation % | Expenditure / Allocation × 100 | Expenditure, Allocation | Fund-utilisation monitoring | Dashboard, risk score |
| Remaining allocation | Allocation − relevant spent/sanctioned | Allocation, Sanctioned/Expenditure | Headroom tracking | Dashboard |
| Sanction delay (days) | Sanction Date − Recommendation Date | Recommended, Sanctioned | Processing-delay detection | Statistics, compliance rule |
| Estimate variance % | (Sanction − Recommended)/Recommended × 100 | Recommended, Sanctioned | Cost-estimate control | Statistics |
| Completion duration (days) | Completion Date − Sanction Date | Sanctioned, Completed | Delay detection | Statistics, predictive model |
| Expenditure-to-sanction % | cumulative Expenditure / Sanction Amount × 100 | Expenditure, Sanctioned | Cost-overrun/utilisation | Rule + statistics |
| Cost deviation % | (Final/cumulative Expenditure − Sanction)/Sanction × 100 | Expenditure/Completed, Sanctioned | Cost-overrun detection | Statistics, risk score |
| Transaction frequency | count of transactions per work/period | Expenditure | Spending-velocity analysis | Time-series |
| Vendor concentration % | vendor value / total relevant expenditure × 100 | Expenditure | Vendor-risk detection | Statistics, graph |
| Amount percentile/z-score | rank/standardise within peer group | Expenditure | Outlier detection | Statistics, ML |
| Rolling expenditure | rolling sum/mean over a time window | Expenditure | Trend/spike detection | Time-series |
| Expenditure growth rate | period-over-period % change | Expenditure | Trend detection | Time-series |
| Work-description similarity score | cosine similarity of embeddings | Recommended/Sanctioned/Completed | Duplicate detection | NLP |
| Duplicate probability | combined similarity + context match score | as above | Duplicate-work risk | NLP + rules |
| Financial-physical mismatch flag | spend vs. completion-status inconsistency | Expenditure, Completed | Reconciliation | Rule |
| Inactivity duration (days) | gap between consecutive expenditure events | Expenditure | Stagnation/delay signal | Statistics, ML |
| Status duration (days) | time in current workflow status | Sanctioned (Status field) | Stuck-in-stage alerting | Rule |
| Historical deviation | this work's current value vs. its own past behaviour | any time-indexed field | Behaviour-shift detection | Time-series |
| Peer deviation | this work vs. category/state/size peer group | any numeric field | Norm deviation (§13) | Statistics |
| Calamity frequency | consent count per MP/calamity type/period | Calamity | Calamity trend | Time-series |
| Calamity amount deviation | consent amount vs. peer calamity events | Calamity | Calamity anomaly | Statistics |
| Data completeness score | % of required fields populated per record | all | Data-quality/compliance signal | Rule |
| Same-day-same-vendor txn count | count of same-date, same-vendor transactions | Expenditure | Duplicate-payment context | Rule + statistics |
| Amount repeat count | count of exact-amount recurrence for an entity | Expenditure | Repeated-payment pattern | Statistics |

---

## 21. Database Design

| Table | Key fields | Notes |
|---|---|---|
| MPs | `mp_id` (PK), name, party, state | Master entity; `mp_alias` child table maps observed spelling variants to `mp_id` |
| Constituencies | `constituency_id` (PK), name, state, `mp_id` (FK) | |
| IDAs | `ida_id` (PK), name, jurisdiction | Implementing/District Authority master |
| Vendors | `vendor_id` (PK), name | `vendor_alias` child table for name-variant resolution |
| Works | `work_id` (PK, canonical), category, description, `mp_id` (FK), `constituency_id` (FK), `ida_id` (FK), `work_id_raw` (original unparsed string, for audit) | The lifecycle anchor entity |
| Recommendations | `work_id` (FK), recommendation_date, recommended_amount | 1:1 with Works (usually) |
| Sanctions | `work_id` (FK), sanction_date, sanction_amount, status | 1:1 with Works (usually) |
| Expenditure | `txn_id` (PK, surrogate), `work_id` (FK), `vendor_id` (FK), txn_date, amount, payment_status | 1:many with Works — the transactional table |
| Completion | `work_id` (FK), completion_date, disbursed_amount, has_evidence, evidence_ref | 1:1 with Works |
| Allocations | `allocation_id` (PK), `mp_id` (FK), period/financial_year, allocated_amount | 1:many per MP over time |
| Calamity Consent | `consent_id` (PK), `mp_id` (FK), calamity_type, consent_date, consent_amount, `work_id` (FK, nullable — often unavailable, see §3) | |
| Alerts | `alert_id` (PK), `work_id` (FK), risk_score, severity, contributing_indicators (JSON), baseline_version, generated_at | One row per alert instance |
| Risk Scores | `work_id` (FK), score_date, cost_risk, payment_risk, vendor_risk, delay_risk, duplicate_risk, compliance_risk, evidence_risk, composite_score | Historical score log, not just current state — needed for trend-of-risk analysis |
| Review Outcomes | `alert_id` (FK), reviewer_id, outcome (valid/dismissed/duplicate/data-quality/investigating), reviewed_at, notes | Feeds §21 model calibration |

Use `work_id` as the backbone foreign key everywhere possible; keep the raw/unparsed source string alongside every canonical ID so any downstream disagreement can be traced back to the original CSV row.

---

## 22. Technical Architecture / Tech Stack

| Layer | Recommended choice | Why |
|---|---|---|
| Data processing | Python + Pandas (Polars for larger production volumes) | Pandas is fastest to build with; Polars gives a straightforward upgrade path once thousands-of-records batch jobs get slow, without a full rewrite |
| Database | PostgreSQL | Relational integrity for the join-heavy schema in §21; mature JSON support for storing `contributing_indicators`; widely supported by BI/dashboard tools |
| ML | scikit-learn (Isolation Forest, LOF, preprocessing) + XGBoost/LightGBM (predictive delay/cost models) | scikit-learn covers the unsupervised layer out of the box; gradient-boosted trees are the standard, well-understood choice for tabular predictive problems and support feature-importance explainability |
| NLP | Sentence-Transformers (e.g., MiniLM/multilingual models) | Pretrained sentence embeddings give strong semantic-similarity performance without training a model from scratch — appropriate given limited labelled data |
| Vector search | FAISS | Enables approximate-nearest-neighbour similarity search so duplicate-work detection scales past pairwise O(n²) comparison at thousands of records (§28) |
| Backend / model serving | FastAPI | Async-friendly Python API layer that sits naturally alongside the Python data/ML stack; easy to expose scoring and alert endpoints to the dashboard |
| Dashboard | React + a charting library (e.g., Recharts/Plotly) for the production build; Streamlit is a reasonable fast prototype for the SIH demo itself | React gives the multi-view, filterable dashboard design in §24 the polish judges expect; Streamlit is faster to stand up if the hackathon timeline is tight — pick one and be explicit about which is the prototype vs. the target production stack |
| Data pipeline / scheduling | Scheduled jobs (cron/Airflow) for the incremental ingestion→rules→scoring flow in §5/§16 | Airflow is justified once there are multiple dependent jobs (ingest → clean → integrate → feature → score) that need retry/monitoring; a simpler cron+script setup is fine for the hackathon demo scale |
| Deployment | Docker containers, deployable to cloud or on-premise | Public-finance data may have on-premise/government-infrastructure requirements — containerising keeps that decision open rather than locking into one cloud provider |

---

## 23. Model Training Strategy (Thousands of Records, No Fraud Labels)

You almost certainly **do not have labelled fraud/non-fraud data**, and should say so plainly to judges rather than pretending otherwise.

- **Unsupervised learning is the starting point:** Isolation Forest/LOF/clustering learn "normal" directly from the unlabelled historical data — no labels required, which is exactly the situation MPLADS data is in today.
- **Statistical/rule-based methods** need no training at all — they encode known compliance logic and distributional norms directly.
- **Semi-supervised learning becomes possible once reviewers start marking alerts** as Valid/Dismissed/Data-quality-issue — these outcomes are a small, evolving, and admittedly **biased** label set (biased toward whatever the model already flagged), so treat them as a way to *recalibrate weights and thresholds* (§18), not as ground truth for training a from-scratch fraud classifier.
- **Supervised learning becomes appropriate later**, once a large enough and reasonably balanced set of reviewer-confirmed outcomes accumulates — at that point a model like logistic regression or gradient boosting over the same feature set can learn which combinations of indicators reviewers actually act on.
- **Human feedback loop:** every alert's reviewer outcome (§21 table) is stored and periodically used to (a) recalibrate risk-score weights, (b) adjust similarity/percentile thresholds that are producing too many false positives, and (c) eventually train the supervised layer described above. This loop is what turns a hand-tuned rule/statistics system into a data-informed one over time, without ever requiring labelled data on day one.

---

## 24. Evaluation

| Component | Metrics |
|---|---|
| Anomaly detection | Precision, recall (against reviewer-confirmed outcomes), false-positive rate, alert-acceptance rate (share of alerts reviewers act on vs. dismiss), reviewer agreement rate across cases |
| Duplicate detection | Precision, recall, and a similarity-threshold sensitivity curve (precision/recall at 0.80, 0.85, 0.90 cosine-similarity cutoffs) to justify the chosen threshold |
| Delay prediction | MAE/RMSE for duration regression; precision/recall if framed as a binary "will be late" classifier |
| Compliance rules | Rule accuracy against manually-audited samples; violation-detection rate (share of known/injected test violations correctly caught) |

**Government-platform principle:** minimise false positives while retaining useful recall — a monitoring tool that cries wolf on legitimate repeated payments (§11) or normal cost variation (§14) will train reviewers to ignore it, which defeats the purpose. Track false-positive rate as a first-class metric alongside recall, not an afterthought.

---

## 25. Explainability

Every alert must show **why**, not just a score. Technically: store each risk-score component (§18) and its underlying comparison baseline alongside the composite score, and render them as a plain-language bullet list, e.g.:

> "High-risk because: (1) Expenditure is 28% above sanctioned amount. (2) Vendor concentration is unusually high relative to peers. (3) Project duration is in the 97th percentile for its category. (4) Work description is highly similar to another work. (5) Completion evidence is missing."

Implementation: for ML components, capture per-feature contribution (e.g., the features with the largest deviation from their peer-group median, or a SHAP-style contribution if using a gradient-boosted model) and translate the top 3–5 into the sentence template above. For rule-engine components, the rule's own description *is* the explanation — no translation needed. For NLP similarity, show the two compared descriptions and the similarity score directly. GenAI/an LLM can be layered on top purely to phrase these structured findings fluently (as both source reports recommend) — it should **never be the source of the underlying numbers**, only their narrator, to avoid inventing unsupported claims.

---

## 26. Dashboard Design

| Dashboard | KPIs / charts / tables | Filters | Alerts / drill-down |
|---|---|---|---|
| Executive Overview | Total allocation/sanctioned/expenditure, national utilisation %, completion rate, high-risk case count, state comparison map, trend sparkline | FY, state | Click-through to state view |
| MP Dashboard | Allocation, utilisation %, recommended/sanctioned/completed counts and value, category mix, personal risk-flag count | FY, category | Click-through to Work 360° |
| Constituency Dashboard | Same as MP view, scoped to constituency; peer comparison within state | FY, category | Click-through |
| Work 360° | Full lifecycle timeline (recommendation → sanction → each expenditure transaction → completion), financial comparison card, risk-score breakdown, similar-works panel | — | Reviewer action buttons (§17) |
| Financial Analytics | Cost-estimate variance distribution, cost-overrun leaderboard, utilisation trend | Category, state, FY | Drill to Work 360° |
| Vendor Analytics | Vendor concentration ranking, transaction-count/value profile, constituency-repeat table | Vendor, category | Drill to transactions |
| Duplicate Work Detector | Candidate-pair list ranked by combined similarity+context score, side-by-side description comparison | Similarity threshold slider | Confirm/reject action |
| Delayed Project Monitor | At-risk queue ranked by duration percentile, expected-vs-elapsed duration chart | Category, state | Drill to Work 360° |
| Compliance Dashboard | Rule-violation counts by rule/severity, trend of violations over time | Rule type, severity | Drill to violating records |
| Early Warning Dashboard | Risk-ranked case queue, severity distribution, new-alerts-today count | Severity, state, MP | Drill to alert detail (§17 example) |
| Calamity Dashboard | Consent trend by calamity type, MP-wise consent totals, anomaly flags | Calamity type, FY | Drill to consent records |

---

## 27. End-to-End Examples

**Example 1 — Cost Overrun.** Recommended ₹3,50,000 → Sanctioned ₹3,80,000 (estimate variance +8.6%, within normal range) → cumulative Expenditure ₹5,02,000 against the ₹3,80,000 sanction (cost overrun +32.1%, category peer 90th percentile is +14%) → `expenditure_anomaly_score` high, `cost_risk` component high → composite Risk Score 78 (🟠 High) → alert generated with the exact percentages and peer benchmark shown → auditor reviews and either confirms a valid revised sanction exists (dismiss) or escalates for investigation.

**Example 2 — Delayed Project.** Recommended 10-Jan → Sanctioned 24-Jan (14-day delay, normal for category) → only one expenditure transaction recorded, 60 days after sanction, then no further activity for 200 days while category peer median sanction-to-completion is 210 days total → predictive delay model, trained on historically-completed works of the same category/state/size, estimates a low probability of on-time completion → `delay_risk` component elevated → early warning issued **before** the work formally breaches any deadline, flagged as "stagnating" with the inactivity-gap number shown.

**Example 3 — Potential Duplicate Work.** Description A: "Construction of community hall, Ward 7, ₹6,20,000, recommended 3-Mar." Description B: "Community centre building work, Ward 7 locality, ₹6,00,000, recommended 9-Mar." → embeddings generated for both → cosine similarity = 0.89 → contextual check: same constituency, same category, amount within 3.3%, dates 6 days apart → all context gates pass → duplicate-work candidate created with both records and the similarity score → routed to the Duplicate Work Detector dashboard for auditor confirmation, not auto-merged or auto-rejected.

---

## 28. Rules vs. Statistics vs. ML vs. NLP vs. Predictive — Which Fits Each Problem

| Problem | Rule-based | Statistical | ML | NLP | Predictive |
|---|---|---|---|---|---|
| Expenditure before/above sanction | ✅ Best fit — unambiguous, deterministic | — | — | — | — |
| Trend detection | — | ✅ Best fit — rolling averages/slopes | Optional (change-point) | — | — |
| Transaction outlier | supporting | ✅ Best fit — percentile/z-score/IQR | ✅ (multivariate cases) | — | — |
| Multivariate anomaly (many features at once) | — | supporting | ✅ Best fit — Isolation Forest/LOF | — | — |
| Duplicate work | supporting (exact ID match) | — | — | ✅ Best fit — embeddings + similarity | — |
| Duplicate payment | ✅ Best fit for exact duplicates | supporting for pattern context | — | — | — |
| Cost overrun | ✅ for the threshold breach itself | ✅ for peer benchmarking | supporting | — | — |
| Delayed project (has it happened) | ✅ vs. official timelines | ✅ vs. peer percentile | supporting | — | — |
| Delay risk (will it happen) | — | — | — | — | ✅ Best fit — regression/survival model |
| Vendor concentration | — | ✅ Best fit — concentration ratio | supporting (network analysis) | — | — |
| Missing/incomplete data | ✅ Best fit | — | — | — | — |
| Norm deviation | — | ✅ Best fit — peer-group baselines | supporting | — | — |
| Explaining an alert | ✅ (rule text) | ✅ (baseline numbers) | supporting (feature contribution) | ✅ (side-by-side text) | — |

**Principle:** don't force ML where a simple rule or a percentile comparison already answers the question transparently and correctly — reserve ML for genuinely multivariate or unstructured (text) problems where no simple rule exists.

---

## 29. Limitations and Data Requirements

| Requirement | Current capability (from supplied samples) | Needed for stronger production detection |
|---|---|---|
| Fund utilisation | Supported conceptually | Actual expenditure linked to work and financial year at production volume |
| Cost overrun | Partially supported | Explicit estimate/revised-estimate/final-expenditure fields |
| Payment anomaly | Foundation present | Transaction-level payments with reliable timestamps at scale |
| Financial-physical mismatch | Requires linkage | Physical-progress data with timestamps, not just a completion date |
| Delay prediction | Lifecycle timing supported | Planned milestones + a large set of historical outcomes |
| Duplicate detection | Strong foundation | Reliable location identifiers + longer history |
| Calamity linkage | Partial | A reliable consent-to-work/expenditure identifier (currently absent) |
| Compliance monitoring | Architecture supported | Official rules, thresholds, and process fields confirmed by the scheme's actual regulations |
| Fraud determination | **Not appropriate from data alone** | Human investigation and corroborating evidence outside this dataset |
| Computer-vision evidence checks | Not currently possible | Actual image files/URLs (only an evidence indicator/flag is in the current sample) |

Production ingestion must also handle: missing values, inconsistent headers (confirmed in the Lok Sabha report for the Recommended/Sanctioned files), date-parsing failures, encoding errors, categorical normalisation, and stable cross-dataset identifiers (§3).

---

## 30. Future Enhancements

- **Computer vision** on completion-evidence images once real image files are supplied — repeated-image detection, basic progress-consistency checks.
- **Graph/network analytics** at production scale — visualise and score MP–vendor–IDA–work relationship graphs to surface concentration patterns invisible in tabular views.
- **GenAI/RAG layer** for natural-language Q&A over the monitoring database and for generating investigation-brief narratives from structured findings (never as the source of the underlying numbers — see §25).
- **Supervised fraud-risk model** once a sufficiently large, reviewer-confirmed outcome dataset accumulates (§23).
- **Streaming/event-based scoring** for newly-ingested transactions, once volumes justify moving off batch-only processing.
- **Calamity-to-work linkage** if the scheme's actual data model is extended with a reliable identifier connecting consent records to downstream expenditure.

---

## 31. Sample Data vs. Real Data — Why This Matters

The supplied CSVs (9–13 rows each) exist to **prove the pipeline design and data model**, not to produce statistically valid conclusions. A percentile, z-score, or ML anomaly score computed on 9–13 rows is not meaningful — there isn't enough data to define a credible "normal" distribution. What the samples *do* prove: the join keys work (8 Work IDs overlap between Recommended and Sanctioned in the actual sample, confirming the lifecycle-linkage design is sound); the specific data-quality issues that must be handled (composite Work ID field, blank trailing rows, inconsistent statuses); and the exact shape every downstream feature and rule will operate on.

At production scale (thousands of records), the same pipeline improves in concrete ways: **baseline estimation** becomes statistically reliable (percentiles and IQR fences reflect genuine typical behaviour rather than a handful of data points); **anomaly detection** models (Isolation Forest/LOF) have enough density to distinguish a genuinely rare pattern from ordinary variation; **predictive models** (delay/cost-risk) have enough historical outcomes to learn from; and the **computational architecture** should shift from ad-hoc pandas scripts on the full table each run to incremental, indexed database queries and approximate-nearest-neighbour search for NLP similarity (§28), because full pairwise comparison and full-table recomputation both become impractical well before "thousands of records" turns into tens of thousands.

---

## 32. SIH Presentation Preparation

**30-second explanation.** "We connect the six MPLADS datasets — allocation, recommendation, sanction, expenditure, completion, and calamity consent — into one work-level lifecycle. Rules catch known violations, statistics and unsupervised ML catch unusual patterns, NLP catches duplicate works, and everything feeds one explainable risk score that prioritises cases for human review — never an automated fraud verdict."

**1-minute explanation.** Add: "The key insight is that most useful signals live in the *transitions* between datasets — a sanctioned amount alone isn't suspicious, but a sanctioned amount that jumped 40% above the estimate, paid out in one burst, to a vendor who's unusually concentrated in that constituency, is. We deliberately use multiple techniques instead of one black-box model because each problem — a known rule, a statistical outlier, free-text similarity, a future-risk prediction — needs a different, explainable tool."

**3-minute technical explanation.** Walk through the pipeline diagram (§5): ingestion → cleaning → entity resolution (explain the Work ID parsing problem you actually found in the data) → feature engineering → the four detection layers (rules, statistics, unsupervised ML, NLP) → risk fusion → early warning → dashboard → human review with a feedback loop back into model calibration. Use one worked example (§27) end-to-end with real numbers.

**5-minute architecture explanation.** Add the database schema (§21), the tech-stack choices and *why* (§22), and the honest limitations table (§29) — judges respond well to a team that states clearly what needs more data rather than overclaiming.

**Judge Q&A prep:**

- *"How exactly does your AI detect fraud?"* — "It doesn't detect fraud; it detects statistically unusual patterns — cost deviations, payment anomalies, vendor concentration, duplicate work — and ranks them for human investigators. Fraud is a legal conclusion; we produce prioritised, explainable leads."
- *"How do you detect trends?"* — Point to §6: rolling averages/slopes on time-bucketed aggregates, distinguished explicitly from single-point anomalies.
- *"Where is ML being used?"* — Isolation Forest/LOF for multivariate financial/temporal anomalies (§8), Sentence-Transformer embeddings for duplicate-work similarity (§10), and (once enough history exists) gradient-boosted models for delay/cost-risk prediction (§12, §21).
- *"Why not just use rules?"* — Rules only catch violations you already know how to define in advance; they can't catch an unusual *combination* of otherwise-normal-looking features, and they can't measure free-text similarity — that's exactly the gap unsupervised ML and NLP fill (§19).
- *"How do you detect duplicate works?"* — Three-stage funnel: exact ID match → fuzzy string match → sentence-embedding cosine similarity, gated by matching location/category/amount/date context to control false positives (§10).
- *"How do you detect cost overruns?"* — Chain the recommended → sanctioned → actual/final amounts, compute variance/overrun percentages, and benchmark against category- and size-specific peer distributions rather than one fixed number (§14).
- *"How do you detect delayed projects?"* — Learn category/state/size-specific duration percentiles from historical data rather than an arbitrary day count, and flag works beyond the 90th/95th percentile of their own peer group (§12).
- *"How do you establish normal behaviour?"* — Peer-group statistical baselines (median, IQR, percentiles), recomputed periodically as production data accumulates, versioned so every alert cites the exact baseline it was compared against (§13).
- *"What happens if you don't have fraud labels?"* — Start fully unsupervised (Isolation Forest/LOF, statistical baselines need no labels); use reviewer outcomes as an evolving, admittedly-biased feedback signal to recalibrate weights and thresholds; move toward supervised learning only once a reasonably sized, reviewer-confirmed outcome set exists (§23).
- *"How does automated compliance work?"* — A deterministic rule table (§16) runs incrementally on every new/changed record, assigns severity, and updates the composite risk score — no ML needed for this layer, deliberately.
- *"How does your early-warning mechanism work?"* — Any medium+ compliance violation or a risk score crossing a calibrated threshold generates an alert object containing the top contributing indicators and their comparison baselines, routed to the relevant dashboard (§17).
- *"How do you prevent false positives?"* — Multi-signal gating (e.g., duplicate-work needs similarity **and** context match, §10), contextual validation before flagging repeated payments (§11), tracking false-positive rate as a first-class evaluation metric (§24), and a human-in-the-loop review queue that feeds back into recalibration.
- *"How does the system scale to thousands of records?"* — Incremental (not full-recompute) scoring jobs, indexed database queries instead of ad-hoc pandas scans, approximate-nearest-neighbour search (FAISS) for NLP similarity instead of pairwise comparison, and periodically recalibrated statistical baselines (§22, §28, §31).

---

## 33. Final End-to-End Implementation Blueprint (Summary Checklist)

1. Build ingestion + cleaning scripts for all six CSVs; handle the specific issues already found (composite Work ID field, blank trailing rows, inconsistent headers/status vocabulary).
2. Build the entity-resolution layer: canonical `work_id`, `mp_id`, `vendor_id`, plus alias tables — this underpins every join.
3. Stand up the PostgreSQL schema from §21 and load the cleaned, resolved data.
4. Implement the feature-engineering job (§20) producing the full feature table per work/transaction.
5. Implement the deterministic rule engine (§16) and confirm it runs incrementally on new/changed records.
6. Implement statistical baselines (§13) segmented by category/state/size, versioned.
7. Train Isolation Forest/LOF on the engineered feature vectors (§8) — clearly labelled as a sample-scale proof-of-concept until production volume exists.
8. Build the duplicate-work NLP pipeline (§10) with the contextual-gating logic.
9. Implement the risk-fusion formula (§18) combining all of the above into one explainable composite score.
10. Build the alert-generation and review-outcome logging flow (§17, §21 Review Outcomes table).
11. Build the dashboard views (§26), starting with Executive Overview, Work 360°, and Early Warning Dashboard as the three the SIH demo should showcase first.
12. Prepare the worked examples (§27) with realistic numbers for the live demo.
13. Prepare the judge Q&A talking points (§32), and be ready to show the limitations table (§29) unprompted — it signals technical maturity rather than a gap in the work.
