# Canonical Feature Store Dictionary
**Version**: `v1.0`

## Table: `features_work`
| Feature Name | Definition | Data Type |
| :--- | :--- | :--- |
| `sanction_delay_days` | Days between recommendation date and sanction date | `Float / Numeric` |
| `completion_delay_days` | Days between sanction date and completion date | `Float / Numeric` |
| `inactivity_gap_days` | Days since latest expenditure or completion | `Float / Numeric` |
| `duration_percentile` | Percentile rank of execution duration within work category | `Integer / String / Boolean` |
| `estimate_variance_pct` | Percentage variance between sanctioned amount and recommended amount | `Float / Numeric` |
| `overrun_pct` | Percentage cost overrun between expenditure amount and sanctioned amount | `Float / Numeric` |
| `has_recommendation` | Boolean flag indicating presence of recommendation stage | `Integer / String / Boolean` |
| `has_sanction` | Boolean flag indicating presence of sanction stage | `Integer / String / Boolean` |
| `has_expenditure` | Boolean flag indicating presence of expenditure stage | `Integer / String / Boolean` |
| `has_completion` | Boolean flag indicating presence of completion stage | `Integer / String / Boolean` |
| `lifecycle_completeness_ratio` | Completeness score from 0.25 to 1.0 based on available stages | `Integer / String / Boolean` |
| `text_length_char` | Character length of work description text | `Integer / String / Boolean` |
| `text_word_count` | Word count of work description text | `Integer / String / Boolean` |

## Table: `features_transaction`
| Feature Name | Definition | Data Type |
| :--- | :--- | :--- |
| `amount_zscore` | Z-score of transaction amount relative to category mean and std | `Float / Numeric` |
| `amount_percentile` | Percentile rank of transaction amount within category | `Integer / String / Boolean` |
| `expenditure_to_sanction_pct` | Percentage of sanctioned amount disbursed in this transaction | `Float / Numeric` |
| `is_round_amount` | Boolean flag if amount is divisible by 10,000 or 100,000 | `Integer / String / Boolean` |
| `days_since_sanction` | Days between sanction date and disbursement date | `Integer / String / Boolean` |
| `days_to_completion` | Days between disbursement date and completion date | `Integer / String / Boolean` |

## Table: `features_vendor`
| Feature Name | Definition | Data Type |
| :--- | :--- | :--- |
| `canonical_vendor_name` | Normalized canonical vendor name | `Integer / String / Boolean` |
| `concentration_pct` | Vendor expenditure share within constituency total spend | `Float / Numeric` |
| `work_count` | Number of works awarded to vendor | `Integer / String / Boolean` |
| `constituency_count` | Number of unique constituencies served | `Integer / String / Boolean` |
| `mp_count` | Number of unique MPs awarding contracts to vendor | `Integer / String / Boolean` |
| `total_expenditure_inr` | Total rupees disbursed to vendor | `Integer / String / Boolean` |
| `avg_work_value_inr` | Average disbursement per work for vendor | `Integer / String / Boolean` |
| `single_mp_dependence_pct` | Percentage of vendor income originating from top MP | `Float / Numeric` |

## Table: `features_mp`
| Feature Name | Definition | Data Type |
| :--- | :--- | :--- |
| `canonical_mp_name` | Normalized canonical MP name | `Integer / String / Boolean` |
| `source_house` | House of Parliament (LOK_SABHA / RAJYA_SABHA) | `Integer / String / Boolean` |
| `utilisation_pct` | Percentage of allocated financial limit spent | `Float / Numeric` |
| `output_per_rupee` | Completed works count per ₹ 1 Crore spent | `Integer / String / Boolean` |
| `recommendation_count` | Total works recommended by MP | `Integer / String / Boolean` |
| `sanction_count` | Total works sanctioned for MP | `Integer / String / Boolean` |
| `completed_count` | Total works completed for MP | `Integer / String / Boolean` |
| `avg_sanction_delay_days` | Mean sanction delay across MP works | `Float / Numeric` |
| `category_entropy` | Shannon entropy score of expenditure across work categories | `Integer / String / Boolean` |
| `top_vendor_concentration_pct` | Share of MP vendor spend awarded to top vendor | `Float / Numeric` |
