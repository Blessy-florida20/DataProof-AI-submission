from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import pandas as pd


DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d %b %Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
)


def _safe_date_parse(value: Any) -> pd.Timestamp | pd.NaT:
    """Parse mixed date formats while preserving ambiguity cues."""
    if pd.isna(value):
        return pd.NaT

    s = str(value).strip()
    if not s:
        return pd.NaT

    # ISO-style date.
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(s, format=fmt)
        except (TypeError, ValueError):
            continue

    # Fallback for pandas parser when text is mixed but still valid.
    try:
        return pd.to_datetime(s, errors="raise")
    except (TypeError, ValueError):
        return pd.NaT


def _is_ambiguous_date(value: Any) -> bool:
    s = str(value).strip()
    if not s:
        return False

    if "/" not in s:
        return False

    parts = s.split("/")
    if len(parts) != 3:
        return False

    try:
        n1, n2, year = [int(p) for p in parts]
    except ValueError:
        return False

    return 1 <= n1 <= 12 and 1 <= n2 <= 12 and n1 != n2


def _compute_revenue_inr(orders_df: pd.DataFrame, fx_df: pd.DataFrame) -> pd.DataFrame:
    merged = orders_df.dropna(subset=["quantity", "unit_price"]).merge(fx_df, on="currency", how="left")
    merged["revenue_inr"] = merged["quantity"] * merged["unit_price"] * merged["rate_to_inr"]
    merged["true_date"] = merged["order_date"].apply(_safe_date_parse)
    return merged


def analyze_data(data_dir: str | os.PathLike[str] = "data") -> Dict[str, Any]:
    base_dir = Path(data_dir)
    orders = pd.read_csv(base_dir / "orders.csv")
    customers = pd.read_csv(base_dir / "customers.csv")
    products = pd.read_csv(base_dir / "products.csv")
    payments = pd.read_csv(base_dir / "payments.csv")
    fx_rates = pd.read_csv(base_dir / "fx_rates.csv")

    duplicated_rows = int(orders.duplicated().sum())
    valid_orders = orders.dropna(subset=["quantity", "unit_price"]).drop_duplicates()

    revenue = _compute_revenue_inr(orders, fx_rates)
    revenue = revenue.merge(customers, on="customer_id", how="left").merge(products, on="product_id", how="left")

    q1 = duplicated_rows
    q2 = int(valid_orders.shape[0])
    q3 = round(float(revenue["revenue_inr"].sum()), 2)
    q4 = round(float(revenue[revenue["segment"] == "Enterprise"]["revenue_inr"].sum()), 2)
    q5 = revenue.groupby("product_name", as_index=False)["revenue_inr"].sum().sort_values("revenue_inr", ascending=False).iloc[0]["product_name"]
    feb = revenue[revenue["true_date"].dt.strftime("%Y-%m").eq("2026-02")]
    q6 = round(float(feb["revenue_inr"].sum()), 2)

    mismatches = payments.merge(
        orders,
        on="order_id",
        how="left",
        suffixes=("_payment", "_order"),
    )
    mismatches = mismatches.dropna(subset=["quantity", "unit_price"])
    mismatches = mismatches[(mismatches["amount_paid"] - mismatches["quantity"] * mismatches["unit_price"]).abs() > 1e-9]
    q7 = int(mismatches.shape[0])

    q8 = "AMBIGUOUS" if any(_is_ambiguous_date(v) for v in orders["order_date"].dropna().unique()) else 0
    q9 = "CANNOT_DETERMINE"
    q10 = "CANNOT_DETERMINE"

    return {
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4,
        "Q5": q5,
        "Q6": q6,
        "Q7": q7,
        "Q8": q8,
        "Q9": q9,
        "Q10": q10,
    }


def main() -> None:
    results = analyze_data(Path(__file__).resolve().parent / "data")
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
