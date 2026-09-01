import os
import glob
from data_pipeline.cleaning.base_cleaner import BaseCleaner

class LokSabhaCleaner(BaseCleaner):
    def __init__(self, raw_dir, cleaned_dir, quarantine_dir):
        super().__init__(
            house_name="LOK_SABHA",
            raw_dir=raw_dir,
            cleaned_dir=cleaned_dir,
            quarantine_dir=quarantine_dir
        )

    def clean_all(self):
        print("\n==========================================")
        print("Starting LOK SABHA Data Cleaning Pipeline...")
        print("==========================================")
        
        file_mapping = {
            "Allocated Limit*.csv": "allocated_limit",
            "Amount consented*.csv": "calamity_consent",
            "Works Recommended*.csv": "works_recommended",
            "Works Sanctioned*.csv": "works_sanctioned",
            "Works Completed*.csv": "works_completed",
            "Expenditure on Completed*.csv": "expenditure"
        }
        
        all_metrics = []
        for pattern, dataset_type in file_mapping.items():
            matches = glob.glob(os.path.join(self.raw_dir, pattern))
            matches = [m for m in matches if "sample" not in os.path.basename(m).lower()]
            if matches:
                filepath = matches[0]
                m = self.process_file(filepath, dataset_type)
                all_metrics.append(m)
            else:
                print(f"[Warning] Lok Sabha dataset pattern not found: {pattern}")
                
        # Save complete audit log
        audit_path = os.path.join("data", "reports", "lok_sabha_cleaning_audit.csv")
        self.audit_logger.save_to_csv(audit_path)
        print(f"[LOK_SABHA] Cleaning audit log saved to {audit_path}")
        return all_metrics

class RajyaSabhaCleaner(BaseCleaner):
    def __init__(self, raw_dir, cleaned_dir, quarantine_dir):
        super().__init__(
            house_name="RAJYA_SABHA",
            raw_dir=raw_dir,
            cleaned_dir=cleaned_dir,
            quarantine_dir=quarantine_dir
        )

    def clean_all(self):
        print("\n==========================================")
        print("Starting RAJYA SABHA Data Cleaning Pipeline...")
        print("==========================================")
        
        file_mapping = {
            "Allocated Limit*.csv": "allocated_limit",
            "Amount consented*.csv": "calamity_consent",
            "Works Recommended*.csv": "works_recommended",
            "Works Sanctioned*.csv": "works_sanctioned",
            "Works Completed*.csv": "works_completed",
            "Expenditure on Completed*.csv": "expenditure"
        }
        
        all_metrics = []
        for pattern, dataset_type in file_mapping.items():
            matches = glob.glob(os.path.join(self.raw_dir, pattern))
            matches = [m for m in matches if "sample" not in os.path.basename(m).lower()]
            if matches:
                filepath = matches[0]
                m = self.process_file(filepath, dataset_type)
                all_metrics.append(m)
            else:
                print(f"[Warning] Rajya Sabha dataset pattern not found: {pattern}")
                
        # Save complete audit log
        audit_path = os.path.join("data", "reports", "rajya_sabha_cleaning_audit.csv")
        self.audit_logger.save_to_csv(audit_path)
        print(f"[RAJYA_SABHA] Cleaning audit log saved to {audit_path}")
        return all_metrics

with open("data_pipeline/cleaning/lok_sabha_cleaner.py", "w", encoding="utf-8") as out:
    out.write('''import os
import glob
from data_pipeline.cleaning.base_cleaner import BaseCleaner

class LokSabhaCleaner(BaseCleaner):
    def __init__(self, raw_dir, cleaned_dir, quarantine_dir):
        super().__init__(
            house_name="LOK_SABHA",
            raw_dir=raw_dir,
            cleaned_dir=cleaned_dir,
            quarantine_dir=quarantine_dir
        )

    def clean_all(self):
        print("\\n==========================================")
        print("Starting LOK SABHA Data Cleaning Pipeline...")
        print("==========================================")
        
        file_mapping = {
            "Allocated Limit*.csv": "allocated_limit",
            "Amount consented*.csv": "calamity_consent",
            "Works Recommended*.csv": "works_recommended",
            "Works Sanctioned*.csv": "works_sanctioned",
            "Works Completed*.csv": "works_completed",
            "Expenditure on Completed*.csv": "expenditure"
        }
        
        all_metrics = []
        for pattern, dataset_type in file_mapping.items():
            matches = glob.glob(os.path.join(self.raw_dir, pattern))
            matches = [m for m in matches if "sample" not in os.path.basename(m).lower()]
            if matches:
                filepath = matches[0]
                m = self.process_file(filepath, dataset_type)
                all_metrics.append(m)
            else:
                print(f"[Warning] Lok Sabha dataset pattern not found: {pattern}")
                
        audit_path = os.path.join("data", "reports", "lok_sabha_cleaning_audit.csv")
        self.audit_logger.save_to_csv(audit_path)
        print(f"[LOK_SABHA] Cleaning audit log saved to {audit_path}")
        return all_metrics
''')

with open("data_pipeline/cleaning/rajya_sabha_cleaner.py", "w", encoding="utf-8") as out:
    out.write('''import os
import glob
from data_pipeline.cleaning.base_cleaner import BaseCleaner

class RajyaSabhaCleaner(BaseCleaner):
    def __init__(self, raw_dir, cleaned_dir, quarantine_dir):
        super().__init__(
            house_name="RAJYA_SABHA",
            raw_dir=raw_dir,
            cleaned_dir=cleaned_dir,
            quarantine_dir=quarantine_dir
        )

    def clean_all(self):
        print("\\n==========================================")
        print("Starting RAJYA SABHA Data Cleaning Pipeline...")
        print("==========================================")
        
        file_mapping = {
            "Allocated Limit*.csv": "allocated_limit",
            "Amount consented*.csv": "calamity_consent",
            "Works Recommended*.csv": "works_recommended",
            "Works Sanctioned*.csv": "works_sanctioned",
            "Works Completed*.csv": "works_completed",
            "Expenditure on Completed*.csv": "expenditure"
        }
        
        all_metrics = []
        for pattern, dataset_type in file_mapping.items():
            matches = glob.glob(os.path.join(self.raw_dir, pattern))
            matches = [m for m in matches if "sample" not in os.path.basename(f).lower() if 'm' in locals() or 'f' in locals()]
            matches = [m for m in glob.glob(os.path.join(self.raw_dir, pattern)) if "sample" not in os.path.basename(m).lower()]
            if matches:
                filepath = matches[0]
                m = self.process_file(filepath, dataset_type)
                all_metrics.append(m)
            else:
                print(f"[Warning] Rajya Sabha dataset pattern not found: {pattern}")
                
        audit_path = os.path.join("data", "reports", "rajya_sabha_cleaning_audit.csv")
        self.audit_logger.save_to_csv(audit_path)
        print(f"[RAJYA_SABHA] Cleaning audit log saved to {audit_path}")
        return all_metrics
''')

print("Created Lok Sabha and Rajya Sabha cleaners!")
