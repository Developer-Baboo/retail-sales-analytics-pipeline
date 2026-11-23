"""Post-load data quality checks. Results are logged and returned as a DataFrame."""
import pandas as pd
from sqlalchemy import text

from db import get_engine, log_step, tbl


def run_checks(engine=None) -> pd.DataFrame:
    engine = engine or get_engine()
    f, s = tbl(engine, "fact_sales"), tbl(engine, "stg_sales")
    p, c, st, d = (tbl(engine, n) for n in ["dim_product", "dim_customer", "dim_store", "dim_date"])

    checks = {
        "Row count: staging == fact": (f"SELECT ABS((SELECT COUNT(*) FROM {s}) - (SELECT COUNT(*) FROM {f}))", 0),
        "Null keys in fact": (f"SELECT COUNT(*) FROM {f} WHERE date_key IS NULL OR product_key IS NULL "
                              "OR customer_key IS NULL OR store_key IS NULL", 0),
        "Duplicate order_id in fact": (f"SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM {f}", 0),
        "Orphan product keys": (f"SELECT COUNT(*) FROM {f} x LEFT JOIN {p} y ON x.product_key=y.product_key "
                                "WHERE y.product_key IS NULL", 0),
        "Orphan customer keys": (f"SELECT COUNT(*) FROM {f} x LEFT JOIN {c} y ON x.customer_key=y.customer_key "
                                 "WHERE y.customer_key IS NULL", 0),
        "Orphan store keys": (f"SELECT COUNT(*) FROM {f} x LEFT JOIN {st} y ON x.store_key=y.store_key "
                              "WHERE y.store_key IS NULL", 0),
        "Orphan date keys": (f"SELECT COUNT(*) FROM {f} x LEFT JOIN {d} y ON x.date_key=y.date_key "
                             "WHERE y.date_key IS NULL", 0),
        "Non-positive quantity": (f"SELECT COUNT(*) FROM {f} WHERE quantity <= 0", 0),
        "Negative revenue": (f"SELECT COUNT(*) FROM {f} WHERE revenue < 0", 0),
        "Discount out of range": (f"SELECT COUNT(*) FROM {f} WHERE discount < 0 OR discount > 0.5", 0),
    }
    results = []
    with engine.connect() as conn:
        for name, (sql, expected) in checks.items():
            val = conn.execute(text(sql)).scalar() or 0
            results.append({"check": name, "value": int(val), "expected": expected,
                            "status": "PASS" if val == expected else "FAIL"})
    df = pd.DataFrame(results)
    failed = int((df["status"] == "FAIL").sum())
    log_step(engine, "data_quality", "SUCCESS" if failed == 0 else "WARN",
             rows_out=len(df) - failed, message=f"{failed} of {len(df)} checks failed")
    return df
