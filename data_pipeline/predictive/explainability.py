import numpy as np

def generate_risk_explanations(df_work, delay_p, cost_p, stag_p):
    explanations = []
    
    for i in range(len(df_work)):
        dp, cp, sp = delay_p[i], cost_p[i], stag_p[i]
        row = df_work.iloc[i]
        
        reasons = []
        if dp >= 0.70:
            reasons.append("High historical sanction/completion delay duration")
        if cp >= 0.70:
            reasons.append("Significant expenditure exceeding sanctioned allocation")
        if sp >= 0.70:
            reasons.append("Long inactivity period post-sanction (>180 days without disbursement)")
        if float(row.get("inactivity_gap_days", 0) or 0) > 100:
            reasons.append("Extended period without recent progress updates")
            
        if not reasons:
            reasons.append("Normal project lifecycle trajectory")
            
        explanations.append("; ".join(reasons[:3]))
        
    return explanations
