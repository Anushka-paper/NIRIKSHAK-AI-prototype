import os
import duckdb

def build_investigation_master():
    """
    Creates a materialized flat view joining multiple tables for the central analytical view.
    In our case, since we only have loksabha_expenditure, we will create it from there.
    """
    print("Building Investigation Master View...")
    project_root = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(project_root, "data_processed", "parliament_data.duckdb")
    
    if not os.path.exists(db_path):
        print("Database not found. Make sure ETL runs first.")
        return

    conn = duckdb.connect(db_path)
    
    # We will try to create a view joining loksabha_expenditure with anomaly_results
    try:
        conn.execute("""
            CREATE OR REPLACE VIEW project_investigations AS
            SELECT 
                l.work_id,
                l.state,
                l.district,
                l.constituency,
                l.mp_name,
                l.work_category,
                l.sanctioned_amount,
                l.expenditure_amount,
                l.status,
                COALESCE(a.is_anomaly, false) as anomaly_flag,
                a.anomaly_score
            FROM loksabha_expenditure l
            LEFT JOIN anomaly_results a ON l.work_id = a.work_id
        """)
        print("Created view: project_investigations")
    except Exception as e:
        print(f"Error creating view: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    build_investigation_master()
