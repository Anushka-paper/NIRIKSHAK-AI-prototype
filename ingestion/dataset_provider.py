import os
import glob
import pandas as pd

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
LS_DIR = os.path.join(DATA_DIR, 'LS_DATASET')
RS_DIR = os.path.join(DATA_DIR, 'RS_DATASET')

_cached_dataset_metrics = {}

def _parse_amount(series):
    return pd.to_numeric(series.astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

def parse_house_folder(folder_path, house_name):
    files = glob.glob(os.path.join(folder_path, '*.csv'))
    files = [f for f in files if 'sample' not in os.path.basename(f).lower()]
    
    metrics = {
        'house_label': house_name,
        'allocated_limit_cr': 0.0,
        'calamity_consent_cr': 0.0,
        'recommended_count': 0,
        'recommended_cr': 0.0,
        'sanctioned_count': 0,
        'sanctioned_cr': 0.0,
        'completed_count': 0,
        'completed_cr': 0.0,
        'expenditure_cr': 0.0,
        'total_mps': 0,
        'total_vendors': 0
    }
    
    for f in files:
        bname = os.path.basename(f)
        try:
            df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False)
        except Exception:
            df = pd.read_csv(f, encoding='latin1', low_memory=False)
            
        if not df.empty and 'grand total' in str(df.iloc[-1].values).lower():
            gt_val_raw = df.iloc[-1].dropna().values[-1]
            gt_amount = float(_parse_amount(pd.Series([gt_val_raw])).iloc[0])
            df_rows = df.iloc[:-1]
        else:
            gt_amount = 0.0
            df_rows = df
            
        if 'Allocated Limit' in bname:
            col = [c for c in df_rows.columns if 'Allocated' in c or 'AMOUNT' in c][0]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['allocated_limit_cr'] = round(amt / 1e7, 2)
            metrics['total_mps'] = int(len(df_rows))
            
        elif 'Calamity' in bname:
            col = [c for c in df_rows.columns if 'Consent' in c or 'Amount' in c][-1]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['calamity_consent_cr'] = round(amt / 1e7, 2)
            
        elif 'Recommended' in bname:
            col = [c for c in df_rows.columns if 'RECOMMENDED' in c or 'Amount' in c or 'AMOUNT' in c][0]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['recommended_count'] = int(len(df_rows))
            metrics['recommended_cr'] = round(amt / 1e7, 2)
            
        elif 'Sanctioned' in bname:
            col = [c for c in df_rows.columns if 'Sanction' in c and ('Amount' in c or 'AMOUNT' in c)][0]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['sanctioned_count'] = int(len(df_rows))
            metrics['sanctioned_cr'] = round(amt / 1e7, 2)
            
        elif 'Completed' in bname and 'Expenditure' not in bname:
            col = [c for c in df_rows.columns if 'Disbursed' in c or 'Amount' in c][0]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['completed_count'] = int(len(df_rows))
            metrics['completed_cr'] = round(amt / 1e7, 2)
            
        elif 'Expenditure' in bname:
            col = [c for c in df_rows.columns if 'Disbursed' in c or 'Amount' in c][0]
            amt = gt_amount if gt_amount > 0 else float(_parse_amount(df_rows[col]).sum())
            metrics['expenditure_cr'] = round(amt / 1e7, 2)
            if 'Vendor Name' in df_rows.columns:
                metrics['total_vendors'] = int(df_rows['Vendor Name'].nunique())
                
    return metrics

def load_all_house_datasets():
    global _cached_dataset_metrics
    ls = parse_house_folder(LS_DIR, 'Lok Sabha')
    rs = parse_house_folder(RS_DIR, 'Rajya Sabha')
    
    comb = {
        'house_label': 'All Houses (Lok Sabha & Rajya Sabha)',
        'allocated_limit_cr': round(ls['allocated_limit_cr'] + rs['allocated_limit_cr'], 2),
        'calamity_consent_cr': round(ls['calamity_consent_cr'] + rs['calamity_consent_cr'], 2),
        'recommended_count': ls['recommended_count'] + rs['recommended_count'],
        'recommended_cr': round(ls['recommended_cr'] + rs['recommended_cr'], 2),
        'sanctioned_count': ls['sanctioned_count'] + rs['sanctioned_count'],
        'sanctioned_cr': round(ls['sanctioned_cr'] + rs['sanctioned_cr'], 2),
        'completed_count': ls['completed_count'] + rs['completed_count'],
        'completed_cr': round(ls['completed_cr'] + rs['completed_cr'], 2),
        'expenditure_cr': round(ls['expenditure_cr'] + rs['expenditure_cr'], 2),
        'total_mps': ls['total_mps'] + rs['total_mps'],
        'total_vendors': ls['total_vendors'] + rs['total_vendors']
    }
    
    _cached_dataset_metrics = {
        'lok_sabha': ls,
        'rajya_sabha': rs,
        'all': comb
    }
    return _cached_dataset_metrics

def get_dataset_metrics(house: str = 'all'):
    if not _cached_dataset_metrics:
        load_all_house_datasets()
    h = house.lower().strip()
    if h in ['lok_sabha', 'loksabha', 'ls']:
        return _cached_dataset_metrics['lok_sabha']
    elif h in ['rajya_sabha', 'rajyasabha', 'rs']:
        return _cached_dataset_metrics['rajya_sabha']
    return _cached_dataset_metrics['all']

load_all_house_datasets()
