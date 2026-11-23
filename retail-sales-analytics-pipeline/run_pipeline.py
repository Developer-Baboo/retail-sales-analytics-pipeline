"""One-command pipeline: generate data -> ETL -> data quality -> Excel report -> AI summary."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import ai_report, data_quality, etl, excel_report, generate_data  # noqa: E402
from db import ROOT, DB_URL  # noqa: E402


def main():
    print(f"Target database: {DB_URL.split('@')[-1] if 'mssql' in DB_URL else DB_URL}")
    raw = ROOT / "data" / "raw_sales.csv"
    if not raw.exists():
        generate_data.generate().to_csv(raw, index=False)
        print(f"[1/5] Generated synthetic data -> {raw.name}")
    stats = etl.run()
    print(f"[2/5] ETL done: {stats}")
    dq = data_quality.run_checks()
    print("[3/5] Data quality checks:\n" + dq.to_string(index=False))
    print(f"[4/5] Excel report -> {excel_report.build()}")
    print(f"[5/5] Executive summary -> {ai_report.build()}")


if __name__ == "__main__":
    main()
