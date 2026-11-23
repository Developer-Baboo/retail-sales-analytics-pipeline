"""AI-assisted executive summary. Uses the Anthropic API if a key is set, otherwise a rule-based fallback."""
import json
import os

import pandas as pd

from db import ROOT
from queries import get_reports


def compute_kpis(r: dict[str, pd.DataFrame]) -> dict:
    m, cat, reg, prod = r["monthly"], r["category"], r["region"], r["top_products"]
    rev, prof = float(m["revenue"].sum()), float(m["profit"].sum())
    best = m.loc[m["revenue"].idxmax()]
    worst = m.loc[m["revenue"].idxmin()]
    return {
        "total_revenue": round(rev, 2), "total_profit": round(prof, 2),
        "margin_pct": round(100 * prof / rev, 1), "orders": int(m["orders"].sum()),
        "best_month": f"{int(best['year'])}-{int(best['month']):02d}", "best_month_revenue": round(float(best["revenue"]), 2),
        "weakest_month": f"{int(worst['year'])}-{int(worst['month']):02d}",
        "top_category": cat.iloc[0]["category"], "top_region": reg.iloc[0]["region"],
        "lowest_margin_category": cat.assign(m=cat["profit"] / cat["revenue"]).sort_values("m").iloc[0]["category"],
        "top_product": prod.iloc[0]["product"],
    }


def rule_based(k: dict) -> str:
    return (f"Revenue totalled {k['total_revenue']:,.0f} across {k['orders']:,} orders at a {k['margin_pct']}% profit margin. "
            f"{k['top_category']} is the leading category and {k['top_region']} the leading region; "
            f"{k['top_product']} is the best-selling product. Peak month was {k['best_month']} and the weakest "
            f"{k['weakest_month']}. {k['lowest_margin_category']} has the lowest margin and deserves a pricing/cost review.")


def ai_summary(k: dict) -> tuple[str, str]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return rule_based(k), "rule-based (no ANTHROPIC_API_KEY set)"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=os.getenv("AI_MODEL", "claude-sonnet-5-5"), max_tokens=500,
            messages=[{"role": "user", "content":
                       "You are a BI analyst. Using ONLY these KPIs, write a 4-sentence executive summary with one "
                       "recommended action. Do not invent numbers.\n" + json.dumps(k)}])
        return msg.content[0].text.strip(), "AI-generated (verify before sharing)"
    except Exception as exc:  # noqa: BLE001
        return rule_based(k), f"rule-based fallback ({type(exc).__name__})"


def build(path=None):
    path = path or ROOT / "output" / "executive_summary.md"
    k = compute_kpis(get_reports())
    text, source = ai_summary(k)
    path.write_text(f"# Executive Summary\n\n_Source: {source}_\n\n{text}\n\n## KPIs\n```json\n{json.dumps(k, indent=2)}\n```\n")
    return path
