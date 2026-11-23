"""Database helpers: SQL Server in production, SQLite for a zero-setup local demo."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_URL = os.getenv("DB_URL", f"sqlite:///{ROOT / 'data' / 'warehouse.db'}")

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS stg_sales (
  order_id TEXT, order_date TEXT, customer_id TEXT, customer_name TEXT, city TEXT, segment TEXT,
  product_id TEXT, product_name TEXT, category TEXT, unit_cost REAL, store_id TEXT, store_name TEXT,
  region TEXT, quantity INTEGER, unit_price REAL, discount REAL);
CREATE TABLE IF NOT EXISTS run_log (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT, run_ts TEXT DEFAULT CURRENT_TIMESTAMP,
  step TEXT, status TEXT, rows_in INTEGER, rows_out INTEGER, message TEXT);
CREATE TABLE IF NOT EXISTS dim_date (date_key INTEGER PRIMARY KEY, full_date TEXT UNIQUE, year INTEGER,
  quarter INTEGER, month INTEGER, month_name TEXT, day INTEGER, day_of_week TEXT);
CREATE TABLE IF NOT EXISTS dim_product (product_key INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id TEXT UNIQUE, product_name TEXT, category TEXT, unit_cost REAL);
CREATE TABLE IF NOT EXISTS dim_customer (customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id TEXT UNIQUE, customer_name TEXT, city TEXT, segment TEXT);
CREATE TABLE IF NOT EXISTS dim_store (store_key INTEGER PRIMARY KEY AUTOINCREMENT,
  store_id TEXT UNIQUE, store_name TEXT, region TEXT);
CREATE TABLE IF NOT EXISTS fact_sales (sales_key INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT UNIQUE,
  date_key INTEGER, product_key INTEGER, customer_key INTEGER, store_key INTEGER, quantity INTEGER,
  unit_price REAL, discount REAL, revenue REAL, cost REAL, profit REAL);
"""


def get_engine():
    if DB_URL.startswith("mssql"):
        return create_engine(DB_URL, fast_executemany=True)
    return create_engine(DB_URL)


def is_mssql(engine) -> bool:
    return engine.dialect.name == "mssql"


def tbl(engine, name: str) -> str:
    """Return schema-qualified table name for SQL Server, plain name for SQLite."""
    schemas = {"stg_sales": "etl", "run_log": "etl"}
    if not is_mssql(engine):
        return name
    return f"{schemas.get(name, 'dw')}.{name}"


def init_local_schema(engine):
    """Create tables for SQLite demo. On SQL Server run sql/01..05 scripts in SSMS instead."""
    if is_mssql(engine):
        return
    with engine.begin() as conn:
        for stmt in SQLITE_SCHEMA.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))


def log_step(engine, step, status, rows_in=None, rows_out=None, message=None):
    with engine.begin() as conn:
        conn.execute(
            text(f"INSERT INTO {tbl(engine, 'run_log')} (step, status, rows_in, rows_out, message) "
                 "VALUES (:s, :st, :ri, :ro, :m)"),
            {"s": step, "st": status, "ri": rows_in, "ro": rows_out, "m": (message or "")[:400]},
        )
