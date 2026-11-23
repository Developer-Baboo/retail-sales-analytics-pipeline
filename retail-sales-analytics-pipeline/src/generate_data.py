"""Generate a realistic, intentionally messy retail sales CSV (synthetic data)."""
import numpy as np
import pandas as pd

from db import ROOT

RNG = np.random.default_rng(42)

PRODUCTS = {  # id: (name, category, cost, price)
    "P001": ("Wireless Mouse", "Electronics", 8, 15), "P002": ("USB-C Cable", "Electronics", 2, 6),
    "P003": ("Bluetooth Speaker", "Electronics", 18, 40), "P004": ("Notebook A5", "Stationery", 1, 3),
    "P005": ("Gel Pens (10 pack)", "Stationery", 2, 5), "P006": ("Desk Organizer", "Home Office", 6, 14),
    "P007": ("LED Desk Lamp", "Home Office", 9, 22), "P008": ("Office Chair", "Home Office", 60, 120),
    "P009": ("Water Bottle", "Lifestyle", 3, 9), "P010": ("Backpack", "Lifestyle", 14, 35),
}
STORES = {"S01": ("Karachi Central", "South"), "S02": ("Lahore Mall", "North"),
          "S03": ("Islamabad Hub", "North"), "S04": ("Hyderabad Outlet", "South"),
          "S05": ("Peshawar Store", "West")}
CITIES = ["Karachi", "Lahore", "Islamabad", "Hyderabad", "Peshawar", "Multan"]
SEGMENTS = ["Consumer", "Corporate", "Small Business"]


def generate(n_rows: int = 20000) -> pd.DataFrame:
    customers = {f"C{i:04d}": (f"Customer {i}", RNG.choice(CITIES), RNG.choice(SEGMENTS)) for i in range(1, 801)}
    dates = pd.to_datetime(RNG.choice(pd.date_range("2024-01-01", "2025-12-31"), n_rows))
    cust_ids = RNG.choice(list(customers), n_rows)
    prod_ids = RNG.choice(list(PRODUCTS), n_rows)
    store_ids = RNG.choice(list(STORES), n_rows)
    rows = []
    for i in range(n_rows):
        pn, cat, cost, price = PRODUCTS[prod_ids[i]]
        cn, city, seg = customers[cust_ids[i]]
        sn, reg = STORES[store_ids[i]]
        rows.append({
            "order_id": f"O{i+1:06d}", "order_date": dates[i].strftime("%Y-%m-%d"),
            "customer_id": cust_ids[i], "customer_name": cn, "city": city, "segment": seg,
            "product_id": prod_ids[i], "product_name": pn, "category": cat, "unit_cost": cost,
            "store_id": store_ids[i], "store_name": sn, "region": reg,
            "quantity": int(RNG.integers(1, 8)), "unit_price": price,
            "discount": float(RNG.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2])),
        })
    df = pd.DataFrame(rows)

    # ---- inject realistic data-quality problems ----
    idx = RNG.choice(df.index, 300, replace=False)
    df.loc[idx[:100], "city"] = None                                   # missing city
    df.loc[idx[100:180], "customer_name"] = df.loc[idx[100:180], "customer_name"].str.upper() + "  "  # casing/space
    df.loc[idx[180:230], "quantity"] = -1                              # invalid quantity
    df.loc[idx[230:260], "order_date"] = "31/12/2025"                  # different date format
    df.loc[idx[260:300], "discount"] = 0.9                             # out-of-range discount
    df = pd.concat([df, df.sample(150, random_state=1)], ignore_index=True)  # duplicate rows
    return df.sample(frac=1, random_state=7).reset_index(drop=True)


if __name__ == "__main__":
    out = ROOT / "data" / "raw_sales.csv"
    generate().to_csv(out, index=False)
    print(f"Wrote {out}")
