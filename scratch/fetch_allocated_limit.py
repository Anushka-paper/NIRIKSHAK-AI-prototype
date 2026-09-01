import pandas as pd
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'raw_csvs'))
ls_alloc_file = os.path.join(base_dir, 'LS_DATASET', 'Allocated Limit for Honble MPs (2).csv')
rs_alloc_file = os.path.join(base_dir, 'RS_DATASET', 'Allocated Limit for Honble MPs (4).csv')

print("==================================================")
print("FETCHING ALLOCATED LIMIT DATA FOR HON'BLE MPs")
print("==================================================")

if os.path.exists(ls_alloc_file):
    df_ls = pd.read_csv(ls_alloc_file)
    amt_col = [c for c in df_ls.columns if 'Allocated' in c][0]
    df_ls['numeric_amt'] = pd.to_numeric(df_ls[amt_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    total_ls_amt = df_ls['numeric_amt'].sum()
    
    print(f"\n--- 1. LOK SABHA ALLOCATION DATA ---")
    print(f"Total MPs Count:    {len(df_ls):,}")
    print(f"Total Allocation:   Rs {total_ls_amt / 10000000.0:,.2f} Crore")
    print(f"Average Allocation: Rs {(total_ls_amt / len(df_ls)) / 100000.0:,.2f} Lakhs per MP\n")
    print("Top 5 Lok Sabha MPs by Allocated Limit:")
    for idx, r in df_ls.sort_values('numeric_amt', ascending=False).head(5).iterrows():
        mp_name = r.iloc[2]
        state = r['State']
        const = r.get('Constituency', '')
        amt_cr = r['numeric_amt'] / 10000000.0
        print(f"  • {mp_name} ({const}, {state}): Rs {amt_cr:.2f} Cr")

if os.path.exists(rs_alloc_file):
    df_rs = pd.read_csv(rs_alloc_file)
    amt_col_rs = [c for c in df_rs.columns if 'Allocated' in c][0]
    df_rs['numeric_amt'] = pd.to_numeric(df_rs[amt_col_rs].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    total_rs_amt = df_rs['numeric_amt'].sum()
    
    print(f"\n\n--- 2. RAJYA SABHA ALLOCATION DATA ---")
    print(f"Total MPs Count:    {len(df_rs):,}")
    print(f"Total Allocation:   Rs {total_rs_amt / 10000000.0:,.2f} Crore")
    print(f"Average Allocation: Rs {(total_rs_amt / len(df_rs)) / 100000.0:,.2f} Lakhs per MP\n")
    print("Top 5 Rajya Sabha MPs by Allocated Limit:")
    for idx, r in df_rs.sort_values('numeric_amt', ascending=False).head(5).iterrows():
        mp_name = r.iloc[2]
        state = r['State']
        cat = r.get('Elected/Nominated', '')
        amt_cr = r['numeric_amt'] / 10000000.0
        print(f"  • {mp_name} ({cat}, {state}): Rs {amt_cr:.2f} Cr")

print("\n==================================================")

