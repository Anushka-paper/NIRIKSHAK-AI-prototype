import type { ConstituencyMPLADS } from "./mplads";

/**
 * Representative mock dataset for MPLADS constituency-level data.
 * Covers major states with realistic fund utilization and anomaly distributions.
 * Replace with real API data from backend_api.py when available.
 */
export const MOCK_CONSTITUENCIES: ConstituencyMPLADS[] = [
  // ── Uttar Pradesh (high risk) ──────────────────────────────────────────────
  {
    id: "UP-01", name: "Lucknow", state: "Uttar Pradesh", mpName: "Rajnath Singh", party: "BJP",
    lat: 26.8467, lng: 80.9462,
    sanctionedAmount: 25, releasedAmount: 22, utilizedAmount: 9.8,
    worksRecommended: 48, worksCompleted: 19, worksPending: 29,
    unspentBalanceAgeMonths: 21,
    anomalyFlags: [
      { type: "fund_diversion", severity: "critical", description: "Funds transferred to non-MPLADS account" },
      { type: "vendor_repeat_pattern", severity: "high", description: "Same vendor awarded 18 of 48 works" },
    ],
  },
  {
    id: "UP-02", name: "Kanpur", state: "Uttar Pradesh", mpName: "Ramesh Awasthi", party: "BJP",
    lat: 26.4499, lng: 80.3319,
    sanctionedAmount: 25, releasedAmount: 20, utilizedAmount: 14.5,
    worksRecommended: 41, worksCompleted: 25, worksPending: 16,
    unspentBalanceAgeMonths: 14,
    anomalyFlags: [
      { type: "inflated_billing", severity: "high", description: "Material costs 3x market rate in 8 works" },
    ],
  },
  {
    id: "UP-03", name: "Varanasi", state: "Uttar Pradesh", mpName: "Narendra Modi", party: "BJP",
    lat: 25.3176, lng: 82.9739,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 21.5,
    worksRecommended: 55, worksCompleted: 48, worksPending: 7,
    unspentBalanceAgeMonths: 4,
    anomalyFlags: [],
  },
  {
    id: "UP-04", name: "Agra", state: "Uttar Pradesh", mpName: "S.P. Singh Baghel", party: "BJP",
    lat: 27.1767, lng: 78.0081,
    sanctionedAmount: 25, releasedAmount: 21, utilizedAmount: 7.2,
    worksRecommended: 36, worksCompleted: 10, worksPending: 26,
    unspentBalanceAgeMonths: 19,
    anomalyFlags: [
      { type: "ghost_works", severity: "critical", description: "6 works show completion certificates but no site evidence" },
      { type: "delayed_utilization", severity: "medium" },
    ],
  },
  {
    id: "UP-05", name: "Mathura", state: "Uttar Pradesh", mpName: "Hema Malini", party: "BJP",
    lat: 27.4924, lng: 77.6737,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 18.2,
    worksRecommended: 44, worksCompleted: 35, worksPending: 9,
    unspentBalanceAgeMonths: 7,
    anomalyFlags: [{ type: "vendor_repeat_pattern", severity: "low" }],
  },

  // ── Maharashtra ──────────────────────────────────────────────────────────────
  {
    id: "MH-01", name: "Mumbai North", state: "Maharashtra", mpName: "Piyush Goyal", party: "BJP",
    lat: 19.2183, lng: 72.8478,
    sanctionedAmount: 25, releasedAmount: 24.5, utilizedAmount: 22,
    worksRecommended: 60, worksCompleted: 54, worksPending: 6,
    unspentBalanceAgeMonths: 3,
    anomalyFlags: [],
  },
  {
    id: "MH-02", name: "Pune", state: "Maharashtra", mpName: "Murlidhar Mohol", party: "BJP",
    lat: 18.5204, lng: 73.8567,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 11.4,
    worksRecommended: 50, worksCompleted: 23, worksPending: 27,
    unspentBalanceAgeMonths: 16,
    anomalyFlags: [
      { type: "inflated_billing", severity: "high" },
      { type: "vendor_repeat_pattern", severity: "medium" },
    ],
  },
  {
    id: "MH-03", name: "Nagpur", state: "Maharashtra", mpName: "Nitin Gadkari", party: "BJP",
    lat: 21.1458, lng: 79.0882,
    sanctionedAmount: 25, releasedAmount: 25, utilizedAmount: 23.8,
    worksRecommended: 52, worksCompleted: 50, worksPending: 2,
    unspentBalanceAgeMonths: 2,
    anomalyFlags: [],
  },
  {
    id: "MH-04", name: "Aurangabad", state: "Maharashtra", mpName: "Chandrakant Khaire", party: "Shiv Sena",
    lat: 19.8762, lng: 75.3433,
    sanctionedAmount: 25, releasedAmount: 19, utilizedAmount: 6.1,
    worksRecommended: 38, worksCompleted: 9, worksPending: 29,
    unspentBalanceAgeMonths: 23,
    anomalyFlags: [
      { type: "fund_diversion", severity: "critical" },
      { type: "ghost_works", severity: "high" },
    ],
  },

  // ── Bihar ──────────────────────────────────────────────────────────────────
  {
    id: "BR-01", name: "Patna Sahib", state: "Bihar", mpName: "Ravi Shankar Prasad", party: "BJP",
    lat: 25.5941, lng: 85.1376,
    sanctionedAmount: 25, releasedAmount: 22, utilizedAmount: 13.2,
    worksRecommended: 45, worksCompleted: 26, worksPending: 19,
    unspentBalanceAgeMonths: 13,
    anomalyFlags: [{ type: "delayed_utilization", severity: "medium" }],
  },
  {
    id: "BR-02", name: "Darbhanga", state: "Bihar", mpName: "Gopal Jee Thakur", party: "BJP",
    lat: 26.1522, lng: 85.8973,
    sanctionedAmount: 25, releasedAmount: 18, utilizedAmount: 5.4,
    worksRecommended: 42, worksCompleted: 9, worksPending: 33,
    unspentBalanceAgeMonths: 22,
    anomalyFlags: [
      { type: "ghost_works", severity: "critical" },
      { type: "inflated_billing", severity: "high" },
      { type: "vendor_repeat_pattern", severity: "medium" },
    ],
  },
  {
    id: "BR-03", name: "Muzaffarpur", state: "Bihar", mpName: "Raj Bhushan Choudhary", party: "BJP",
    lat: 26.1209, lng: 85.3647,
    sanctionedAmount: 25, releasedAmount: 21, utilizedAmount: 10.8,
    worksRecommended: 40, worksCompleted: 18, worksPending: 22,
    unspentBalanceAgeMonths: 17,
    anomalyFlags: [{ type: "delayed_utilization", severity: "high" }],
  },

  // ── Rajasthan ──────────────────────────────────────────────────────────────
  {
    id: "RJ-01", name: "Jaipur", state: "Rajasthan", mpName: "Madan Lal Saini", party: "BJP",
    lat: 26.9124, lng: 75.7873,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 20.1,
    worksRecommended: 48, worksCompleted: 40, worksPending: 8,
    unspentBalanceAgeMonths: 6,
    anomalyFlags: [{ type: "vendor_repeat_pattern", severity: "low" }],
  },
  {
    id: "RJ-02", name: "Jodhpur", state: "Rajasthan", mpName: "Gajendra Singh Shekhawat", party: "BJP",
    lat: 26.2389, lng: 73.0243,
    sanctionedAmount: 25, releasedAmount: 22, utilizedAmount: 16.5,
    worksRecommended: 44, worksCompleted: 32, worksPending: 12,
    unspentBalanceAgeMonths: 9,
    anomalyFlags: [],
  },
  {
    id: "RJ-03", name: "Bharatpur", state: "Rajasthan", mpName: "Ramswarup Koli", party: "BJP",
    lat: 27.2152, lng: 77.5030,
    sanctionedAmount: 25, releasedAmount: 20, utilizedAmount: 8.8,
    worksRecommended: 36, worksCompleted: 13, worksPending: 23,
    unspentBalanceAgeMonths: 18,
    anomalyFlags: [
      { type: "inflated_billing", severity: "high" },
      { type: "fund_diversion", severity: "medium" },
    ],
  },

  // ── Madhya Pradesh ─────────────────────────────────────────────────────────
  {
    id: "MP-01", name: "Bhopal", state: "Madhya Pradesh", mpName: "Alok Sharma", party: "BJP",
    lat: 23.2599, lng: 77.4126,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 19.8,
    worksRecommended: 46, worksCompleted: 41, worksPending: 5,
    unspentBalanceAgeMonths: 4,
    anomalyFlags: [],
  },
  {
    id: "MP-02", name: "Indore", state: "Madhya Pradesh", mpName: "Shankar Lalwani", party: "BJP",
    lat: 22.7196, lng: 75.8577,
    sanctionedAmount: 25, releasedAmount: 25, utilizedAmount: 24.1,
    worksRecommended: 58, worksCompleted: 56, worksPending: 2,
    unspentBalanceAgeMonths: 1,
    anomalyFlags: [],
  },
  {
    id: "MP-03", name: "Gwalior", state: "Madhya Pradesh", mpName: "Vivek Narayan Shejwalkar", party: "BJP",
    lat: 26.2183, lng: 78.1828,
    sanctionedAmount: 25, releasedAmount: 21, utilizedAmount: 9.3,
    worksRecommended: 39, worksCompleted: 14, worksPending: 25,
    unspentBalanceAgeMonths: 20,
    anomalyFlags: [
      { type: "ghost_works", severity: "critical" },
      { type: "vendor_repeat_pattern", severity: "high" },
    ],
  },

  // ── Tamil Nadu ─────────────────────────────────────────────────────────────
  {
    id: "TN-01", name: "Chennai North", state: "Tamil Nadu", mpName: "Kalanidhi Veeraswamy", party: "DMK",
    lat: 13.1067, lng: 80.2206,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 22.5,
    worksRecommended: 55, worksCompleted: 51, worksPending: 4,
    unspentBalanceAgeMonths: 3,
    anomalyFlags: [],
  },
  {
    id: "TN-02", name: "Coimbatore", state: "Tamil Nadu", mpName: "Ganeshamurthi K", party: "AIADMK",
    lat: 11.0168, lng: 76.9558,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 17.9,
    worksRecommended: 48, worksCompleted: 36, worksPending: 12,
    unspentBalanceAgeMonths: 10,
    anomalyFlags: [{ type: "delayed_utilization", severity: "medium" }],
  },
  {
    id: "TN-03", name: "Vellore", state: "Tamil Nadu", mpName: "Kathir Anand", party: "DMK",
    lat: 12.9165, lng: 79.1325,
    sanctionedAmount: 25, releasedAmount: 20, utilizedAmount: 6.8,
    worksRecommended: 37, worksCompleted: 10, worksPending: 27,
    unspentBalanceAgeMonths: 21,
    anomalyFlags: [
      { type: "fund_diversion", severity: "critical" },
      { type: "inflated_billing", severity: "high" },
    ],
  },

  // ── Karnataka ─────────────────────────────────────────────────────────────
  {
    id: "KA-01", name: "Bangalore Central", state: "Karnataka", mpName: "P.C. Mohan", party: "BJP",
    lat: 12.9716, lng: 77.5946,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 21.2,
    worksRecommended: 50, worksCompleted: 44, worksPending: 6,
    unspentBalanceAgeMonths: 5,
    anomalyFlags: [],
  },
  {
    id: "KA-02", name: "Tumkur", state: "Karnataka", mpName: "V. Somanna", party: "BJP",
    lat: 13.3409, lng: 77.1010,
    sanctionedAmount: 25, releasedAmount: 22, utilizedAmount: 14.8,
    worksRecommended: 43, worksCompleted: 28, worksPending: 15,
    unspentBalanceAgeMonths: 11,
    anomalyFlags: [{ type: "vendor_repeat_pattern", severity: "medium" }],
  },
  {
    id: "KA-03", name: "Bellary", state: "Karnataka", mpName: "Y. Devendrappa", party: "BJP",
    lat: 15.1394, lng: 76.9214,
    sanctionedAmount: 25, releasedAmount: 19, utilizedAmount: 7.1,
    worksRecommended: 40, worksCompleted: 11, worksPending: 29,
    unspentBalanceAgeMonths: 20,
    anomalyFlags: [
      { type: "inflated_billing", severity: "critical" },
      { type: "ghost_works", severity: "high" },
    ],
  },

  // ── West Bengal ───────────────────────────────────────────────────────────
  {
    id: "WB-01", name: "Kolkata North", state: "West Bengal", mpName: "Sudip Bandyopadhyay", party: "TMC",
    lat: 22.5726, lng: 88.3639,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 19.4,
    worksRecommended: 52, worksCompleted: 44, worksPending: 8,
    unspentBalanceAgeMonths: 6,
    anomalyFlags: [],
  },
  {
    id: "WB-02", name: "Murshidabad", state: "West Bengal", mpName: "Abu Taher Khan", party: "TMC",
    lat: 24.1800, lng: 88.2800,
    sanctionedAmount: 25, releasedAmount: 18, utilizedAmount: 7.6,
    worksRecommended: 46, worksCompleted: 14, worksPending: 32,
    unspentBalanceAgeMonths: 22,
    anomalyFlags: [
      { type: "fund_diversion", severity: "critical" },
      { type: "vendor_repeat_pattern", severity: "high" },
    ],
  },

  // ── Gujarat ───────────────────────────────────────────────────────────────
  {
    id: "GJ-01", name: "Ahmedabad East", state: "Gujarat", mpName: "Hasmukhbhai Patel", party: "BJP",
    lat: 23.0225, lng: 72.5714,
    sanctionedAmount: 25, releasedAmount: 25, utilizedAmount: 23.6,
    worksRecommended: 54, worksCompleted: 52, worksPending: 2,
    unspentBalanceAgeMonths: 2,
    anomalyFlags: [],
  },
  {
    id: "GJ-02", name: "Surat", state: "Gujarat", mpName: "Mukesh Dalal", party: "BJP",
    lat: 21.1702, lng: 72.8311,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 22.8,
    worksRecommended: 56, worksCompleted: 54, worksPending: 2,
    unspentBalanceAgeMonths: 1,
    anomalyFlags: [],
  },
  {
    id: "GJ-03", name: "Vadodara", state: "Gujarat", mpName: "Hemang Joshi", party: "BJP",
    lat: 22.3072, lng: 73.1812,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 18.7,
    worksRecommended: 46, worksCompleted: 37, worksPending: 9,
    unspentBalanceAgeMonths: 8,
    anomalyFlags: [{ type: "delayed_utilization", severity: "low" }],
  },

  // ── Delhi ─────────────────────────────────────────────────────────────────
  {
    id: "DL-01", name: "New Delhi", state: "Delhi", mpName: "Bansuri Swaraj", party: "BJP",
    lat: 28.6139, lng: 77.2090,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 21.3,
    worksRecommended: 50, worksCompleted: 46, worksPending: 4,
    unspentBalanceAgeMonths: 4,
    anomalyFlags: [],
  },
  {
    id: "DL-02", name: "East Delhi", state: "Delhi", mpName: "Harsh Malhotra", party: "BJP",
    lat: 28.6600, lng: 77.3200,
    sanctionedAmount: 25, releasedAmount: 23, utilizedAmount: 12.1,
    worksRecommended: 44, worksCompleted: 22, worksPending: 22,
    unspentBalanceAgeMonths: 14,
    anomalyFlags: [{ type: "delayed_utilization", severity: "high" }],
  },

  // ── Odisha ────────────────────────────────────────────────────────────────
  {
    id: "OR-01", name: "Bhubaneswar", state: "Odisha", mpName: "Aparajita Sarangi", party: "BJP",
    lat: 20.2961, lng: 85.8245,
    sanctionedAmount: 25, releasedAmount: 22, utilizedAmount: 18.5,
    worksRecommended: 45, worksCompleted: 38, worksPending: 7,
    unspentBalanceAgeMonths: 6,
    anomalyFlags: [],
  },
  {
    id: "OR-02", name: "Kalahandi", state: "Odisha", mpName: "Malvika Devi", party: "BJP",
    lat: 19.9104, lng: 83.1642,
    sanctionedAmount: 25, releasedAmount: 17, utilizedAmount: 6.2,
    worksRecommended: 40, worksCompleted: 10, worksPending: 30,
    unspentBalanceAgeMonths: 24,
    anomalyFlags: [
      { type: "ghost_works", severity: "critical" },
      { type: "delayed_utilization", severity: "critical" },
    ],
  },

  // ── Telangana ─────────────────────────────────────────────────────────────
  {
    id: "TS-01", name: "Hyderabad", state: "Telangana", mpName: "Asaduddin Owaisi", party: "AIMIM",
    lat: 17.3850, lng: 78.4867,
    sanctionedAmount: 25, releasedAmount: 24, utilizedAmount: 22.1,
    worksRecommended: 55, worksCompleted: 51, worksPending: 4,
    unspentBalanceAgeMonths: 3,
    anomalyFlags: [],
  },
  {
    id: "TS-02", name: "Nizamabad", state: "Telangana", mpName: "D. Arvind", party: "BJP",
    lat: 18.6725, lng: 78.0940,
    sanctionedAmount: 25, releasedAmount: 21, utilizedAmount: 10.5,
    worksRecommended: 42, worksCompleted: 18, worksPending: 24,
    unspentBalanceAgeMonths: 16,
    anomalyFlags: [
      { type: "inflated_billing", severity: "high" },
      { type: "vendor_repeat_pattern", severity: "medium" },
    ],
  },
];
