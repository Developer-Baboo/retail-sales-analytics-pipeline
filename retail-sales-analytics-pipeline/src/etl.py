"""Extract -> Transform -> Load. Cleans raw CSV, loads staging, builds the star schema."""
import pandas as pd
from sqlalchemy import text

from db import ROOT, get_engine, init_local_schema, is_mssql, log_step, tbl

RAW = ROOT / "data" / "raw_sales.csv"


def extract(path=RAW) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats = {"raw_rows": len(df)}
    df = df.copy()

    # text standardisation
    for c in ["customer_name", "city", "segment", "product_name", "category", "store_name", "region"]:
        df[c] = df[c].str.strip().str.title()
    df["city"] = df["city"].fillna("Unknown")

    # types
    for c in ["unit_cost", "unit_price", "discount"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    # dates: accept ISO first, then day-first fallback
    iso = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
    alt = pd.to_datetime(df["order_date"], format="%d/%m/%Y", errors="coerce")
    df["order_date"] = iso.fillna(alt)

    # drop exact duplicate rows, then duplicate order ids
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="order_id", keep="first")
    stats["duplicates_removed"] = before - len(df)

    # business rules
    before = len(df)
    df = df[(df["quantity"] > 0) & df["order_date"].notna() & (df["unit_price"] > 0)]
    stats["invalid_rows_removed"] = before - len(df)
    stats["discounts_capped"] = int((df["discount"] > 0.5).sum())
    df["discount"] = df["discount"].clip(0, 0.5).fillna(0)

    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    df["quantity"] = df["quantity"].astype(int)
    stats["clean_rows"] = len(df)
    return df.reset_index(drop=True), stats


def load(df: pd.DataFrame, engine) -> int:
    stg = tbl(engine, "stg_sales")
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {stg}"))
    schema = "etl" if is_mssql(engine) else None
    df.to_sql("stg_sales", engine, schema=schema, if_exists="append", index=False, chunksize=2000)

    if is_mssql(engine):
        with engine.begin() as conn:
            conn.execute(text("EXEC etl.usp_load_star_schema"))
    else:
        script = (ROOT / "sql" / "sqlite_load.sql").read_text()
        with engine.begin() as conn:
            for stmt in script.split(";\n"):
                if stmt.strip():
                    conn.execute(text(stmt))
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {tbl(engine, 'fact_sales')}")).scalar()


def run() -> dict:
    engine = get_engine()
    init_local_schema(engine)
    try:
        raw = extract()
        clean, stats = transform(raw)
        fact_rows = load(clean, engine)
        stats["fact_rows"] = fact_rows
        log_step(engine, "etl", "SUCCESS", stats["raw_rows"], fact_rows, str(stats))
        return stats
    except Exception as exc:  # noqa: BLE001
        log_step(engine, "etl", "FAILED", message=str(exc))
        raise
