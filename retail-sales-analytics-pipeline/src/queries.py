"""Reporting queries (portable across SQL Server and SQLite)."""
import pandas as pd

from db import get_engine, tbl


def _frames(engine):
    f, p, s, d = (tbl(engine, n) for n in ["fact_sales", "dim_product", "dim_store", "dim_date"])
    base = f"FROM {f} f JOIN {d} d ON d.date_key=f.date_key JOIN {p} p ON p.product_key=f.product_key " \
           f"JOIN {s} s ON s.store_key=f.store_key"
    return base


def get_reports(engine=None) -> dict[str, pd.DataFrame]:
    engine = engine or get_engine()
    base = _frames(engine)
    q = {
        "monthly": f"SELECT d.year AS year, d.month AS month, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit, "
                   f"COUNT(*) AS orders {base} GROUP BY d.year, d.month ORDER BY d.year, d.month",
        "category": f"SELECT p.category AS category, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit, "
                    f"SUM(f.quantity) AS units {base} GROUP BY p.category ORDER BY revenue DESC",
        "region": f"SELECT s.region AS region, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit "
                  f"{base} GROUP BY s.region ORDER BY revenue DESC",
        "top_products": f"SELECT p.product_name AS product, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit "
                        f"{base} GROUP BY p.product_name ORDER BY revenue DESC",
    }
    return {k: pd.read_sql(v, engine) for k, v in q.items()}
