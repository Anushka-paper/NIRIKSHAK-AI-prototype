import pandas as pd
import os

base = os.path.dirname(os.path.abspath(__file__))

df = pd.read_csv(os.path.join(base, 'data/predictions/lok_sabha/work_anomalies.csv'), low_memory=False)

STATE_COORDS = {
    'Andaman And Nicobar Islands': (11.7401, 92.6586),
    'Andhra Pradesh': (15.9129, 79.7400),
    'Arunachal Pradesh': (28.2180, 94.7278),
    'Assam': (26.2006, 92.9376),
    'Bihar': (25.0961, 85.3131),
    'Chandigarh': (30.7333, 76.7794),
    'Chhattisgarh': (21.2787, 81.8661),
    'Delhi': (28.7041, 77.1025),
    'Goa': (15.2993, 74.1240),
    'Gujarat': (22.2587, 71.1924),
    'Haryana': (29.0588, 76.0856),
    'Himachal Pradesh': (31.1048, 77.1734),
    'Jammu And Kashmir': (33.7782, 76.5762),
    'Jharkhand': (23.6102, 85.2799),
    'Karnataka': (15.3173, 75.7139),
    'Kerala': (10.8505, 76.2711),
    'Ladakh': (34.1526, 77.5770),
    'Lakshadweep': (10.5667, 72.6417),
    'Madhya Pradesh': (22.9734, 78.6569),
    'Maharashtra': (19.7515, 75.7139),
    'Manipur': (24.6637, 93.9063),
    'Meghalaya': (25.4670, 91.3662),
    'Mizoram': (23.1645, 92.9376),
    'Nagaland': (26.1584, 94.5624),
    'Odisha': (20.9517, 85.0985),
    'Puducherry': (11.9416, 79.8083),
    'Punjab': (31.1471, 75.3412),
    'Rajasthan': (27.0238, 74.2179),
    'Sikkim': (27.5330, 88.5122),
    'Tamil Nadu': (11.1271, 78.6569),
    'Telangana': (18.1124, 79.0193),
    'The Dadra And Nagar Haveli And Daman And Diu': (20.1809, 73.0169),
    'Tripura': (23.9408, 91.9882),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Uttarakhand': (30.0668, 79.0193),
    'West Bengal': (22.9868, 87.8550),
}

stats = df.groupby('state').agg(
    total=('work_id', 'count'),
    anomalies=('is_anomaly', 'sum'),
    avg_score=('anomaly_score', 'mean'),
    sanction_sum=('sanction_amount', 'sum'),
    expenditure_sum=('total_expenditure', 'sum'),
).reset_index()

out_lines = []
out_lines.append("import { ConstituencyMPLADS } from './mplads';")
out_lines.append("")
out_lines.append("// Auto-generated from real MPLADS dataset - all 36 states/UTs")
out_lines.append("export const MOCK_CONSTITUENCIES: ConstituencyMPLADS[] = [")

for _, row in stats.iterrows():
    state = str(row['state'])
    total = int(row['total'])
    anomalies = int(row['anomalies'])
    avg_score = float(row['avg_score'])
    sanction_cr = round(float(row['sanction_sum']) / 1e7, 1)
    expend_cr = round(float(row['expenditure_sum']) / 1e7, 1)
    lat, lng = STATE_COORDS.get(state, (20.5937, 78.9629))

    if avg_score >= 0.7:
        flags = "{ type: 'fund_diversion', severity: 'critical' }"
    elif avg_score >= 0.5:
        flags = "{ type: 'inflated_billing', severity: 'high' }"
    elif avg_score >= 0.3:
        flags = "{ type: 'delayed_utilization', severity: 'medium' }"
    elif anomalies > 0:
        flags = "{ type: 'other', severity: 'low' }"
    else:
        flags = ""

    utilized = expend_cr if expend_cr > 0 else round(sanction_cr * 0.6, 1)
    released = round(sanction_cr * 0.85, 1)
    completed = max(0, total - anomalies - int(total * 0.1))
    pending = total - completed
    age = min(36, max(6, int(avg_score * 36)))
    slug = state.lower().replace(' ', '_')

    out_lines.append("  {")
    out_lines.append(f"    id: '{slug}', name: '{state}', state: '{state}',")
    out_lines.append(f"    mpName: 'Multiple MPs', party: '',")
    out_lines.append(f"    lat: {lat}, lng: {lng},")
    out_lines.append(f"    sanctionedAmount: {sanction_cr}, releasedAmount: {released},")
    out_lines.append(f"    utilizedAmount: {utilized},")
    out_lines.append(f"    worksRecommended: {total}, worksCompleted: {completed}, worksPending: {pending},")
    out_lines.append(f"    unspentBalanceAgeMonths: {age},")
    out_lines.append(f"    anomalyFlags: [{flags}],")
    out_lines.append(f"    lastUpdated: 'Sep 2026',")
    out_lines.append("  },")

out_lines.append("];")

output_path = os.path.join(base, 'frontend/src/lib/mock-constituencies.ts')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f'Done! Generated {len(stats)} state entries -> {output_path}')
