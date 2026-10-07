"""Generates the messy multi-table dataset + answer key for DataProof AI.
Run:  python gen_data.py     (re-run any time; output is deterministic)

TRAPS PLANTED (so you can show judges you handle each):
  1. Units:        orders are in INR, USD and EUR  -> fx_rates.csv needed
  2. Ambiguous dates: '03/04/2026', '05/06/2026' (day/month or month/day?)
  3. Mixed date formats: ISO, 15/02/2026, '5 Jan 2026'
  4. Duplicates:   2 exact duplicate order rows
  5. Missing data: 1 missing quantity, 1 missing unit_price
  6. Contradiction: payments.csv disagrees with orders for 2 orders
  7. No valid answer: no cost/profit columns anywhere
  8. Trick question: region 'Mars' does not exist
"""
import os
import pandas as pd

os.makedirs("data", exist_ok=True)

customers = pd.DataFrame([
    ("C01", "Asha Traders",   "Retail",     "India"),
    ("C02", "BlueWave Ltd",   "Enterprise", "USA"),
    ("C03", "Kiran Stores",   "Retail",     "India"),
    ("C04", "Nordtech GmbH",  "Enterprise", "Germany"),
    ("C05", "Meena Mart",     "Retail",     "India"),
    ("C06", "Globex Corp",    "Enterprise", "USA"),
    ("C07", "Ravi Electronics", "Retail",   "India"),
    ("C08", "Berlin Systems", "Enterprise", "Germany"),
], columns=["customer_id", "name", "segment", "country"])

products = pd.DataFrame([
    ("P1", "Laptop",   "Computers"),
    ("P2", "Mouse",    "Accessories"),
    ("P3", "Keyboard", "Accessories"),
    ("P4", "Monitor",  "Displays"),
], columns=["product_id", "product_name", "category"])

fx = pd.DataFrame([("INR", 1.0), ("USD", 83.0), ("EUR", 90.0)],
                  columns=["currency", "rate_to_inr"])

# (order_id, shown_date, true_date, cust, prod, qty, unit_price, currency, region)
rows = [
 ("O-1001", "2026-01-02", "2026-01-02", "C01", "P1", 2, 55000, "INR", "South"),
 ("O-1002", "2026-01-03", "2026-01-03", "C02", "P2", 5, 12,    "USD", "North"),
 ("O-1003", "5 Jan 2026", "2026-01-05", "C03", "P1", 1, 55000, "INR", "South"),
 ("O-1004", "2026-01-08", "2026-01-08", "C04", "P3", 3, 25,    "EUR", "East"),
 ("O-1005", "2026-01-10", "2026-01-10", "C05", "P1", 1, 55000, "INR", "West"),
 ("O-1006", "2026-01-12", "2026-01-12", "C06", "P4", 2, 150,   "USD", "North"),
 ("O-1007", "2026-01-15", "2026-01-15", "C07", "P2", 4, 800,   "INR", "South"),
 ("O-1008", "2026-01-18", "2026-01-18", "C04", "P3", None, 25, "EUR", "East"),      # missing qty
 ("O-1009", "03/04/2026", "2026-03-04", "C02", "P4", 1, 150,   "USD", "West"),      # AMBIGUOUS date
 ("O-1010", "2026-01-20", "2026-01-20", "C08", "P4", 1, 140,   "EUR", "West"),
 ("O-1011", "2026-02-01", "2026-02-01", "C03", "P1", 1, 55000, "INR", "North"),
 ("O-1012", "2026-02-03", "2026-02-03", "C06", "P2", 10, 12,   "USD", "East"),
 ("O-1013", "2026-02-06", "2026-02-06", "C05", "P3", 2, 1500,  "INR", "South"),
 ("O-1014", "2026-02-09", "2026-02-09", "C02", "P4", 3, 150,   "USD", "South"),
 ("O-1015", "2026-02-11", "2026-02-11", "C07", "P1", 1, None,  "INR", "East"),      # missing price
 ("O-1016", "15/02/2026", "2026-02-15", "C08", "P2", 6, 11,    "EUR", "West"),
 ("O-1017", "2026-02-18", "2026-02-18", "C01", "P4", 1, 12000, "INR", "North"),
 ("O-1018", "2026-02-20", "2026-02-20", "C04", "P3", 4, 25,    "EUR", "West"),
 ("O-1019", "2026-02-25", "2026-02-25", "C06", "P1", 2, 700,   "USD", "South"),
 ("O-1020", "2026-03-02", "2026-03-02", "C05", "P2", 3, 800,   "INR", "North"),
 ("O-1021", "05/06/2026", "2026-06-05", "C01", "P3", 2, 1500,  "INR", "East"),      # AMBIGUOUS date
 ("O-1022", "2026-03-05", "2026-03-05", "C08", "P1", 1, 640,   "EUR", "East"),
]
cols = ["order_id", "order_date", "customer_id", "product_id",
        "quantity", "unit_price", "currency", "region"]
orders = pd.DataFrame([(r[0], r[1], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows],
                      columns=["order_id", "order_date", "customer_id", "product_id",
                               "quantity", "unit_price", "currency", "region"])
# NOTE: tuple index fix -> customer is r[3], product r[4]
orders = pd.DataFrame([(r[0], r[1], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows], columns=cols)

# duplicates: exact copies of 2 rows
orders = pd.concat([orders, orders.iloc[[4]], orders.iloc[[11]]], ignore_index=True)

# payments: one per order; two orders contradict
pay = []
for i, r in enumerate(rows, 1):
    q, p = r[5], r[6]
    amt = (q * p) if (q is not None and p is not None) else None
    if r[0] == "O-1006":
        amt = 250          # should be 300 -> contradiction
    if r[0] == "O-1013":
        amt = 2500         # should be 3000 -> contradiction
    if amt is None:
        amt = 100
    pay.append((f"PAY-{i:03d}", r[0], amt, r[7], r[2]))
payments = pd.DataFrame(pay, columns=["payment_id", "order_id", "amount_paid", "currency", "paid_date"])

for name, df in [("orders", orders), ("customers", customers), ("products", products),
                 ("payments", payments), ("fx_rates", fx)]:
    df.to_csv(f"data/{name}.csv", index=False)

# ---------------- answer key (ground truth, computed from the clean truth) -------------
truth = pd.DataFrame(rows, columns=["order_id", "shown", "true_date", "customer_id", "product_id",
                                    "quantity", "unit_price", "currency", "region"])
ok = truth.dropna(subset=["quantity", "unit_price"]).merge(fx, on="currency")
ok["rev_inr"] = ok["quantity"] * ok["unit_price"] * ok["rate_to_inr"]
ok = ok.merge(customers, on="customer_id").merge(products, on="product_id")

mism = payments.merge(truth, on="order_id").dropna(subset=["quantity", "unit_price"])
mism = mism[(mism["amount_paid"] - mism["quantity"] * mism["unit_price"]).abs() > 1e-9]

key = [
 ("Q1", "How many duplicate order rows are there?", "ANSWER", 2),
 ("Q2", "How many unique valid orders (with quantity and price) are there?", "ANSWER", len(ok)),
 ("Q3", "What is the total revenue in INR across all currencies?", "ANSWER", round(ok.rev_inr.sum(), 2)),
 ("Q4", "What is the total revenue in INR from Enterprise customers?", "ANSWER",
        round(ok[ok.segment == "Enterprise"].rev_inr.sum(), 2)),
 ("Q5", "Which product generated the highest revenue in INR?", "ANSWER",
        ok.groupby("product_name").rev_inr.sum().idxmax()),
 ("Q6", "What was the total revenue in INR in February 2026?", "ANSWER",
        round(ok[ok.true_date.str.startswith("2026-02")].rev_inr.sum(), 2)),
 ("Q7", "For how many orders do payments disagree with the order amount?", "ANSWER", len(mism)),
 ("Q8", "How many orders were placed on 03/04/2026?", "AMBIGUOUS", ""),
 ("Q9", "What was the profit margin?", "CANNOT_DETERMINE", ""),
 ("Q10", "What was the total revenue in the Mars region?", "CANNOT_DETERMINE", ""),
]
pd.DataFrame(key, columns=["id", "question", "expected_status", "expected_value"]).to_csv(
    "answer_key.csv", index=False)

print(pd.DataFrame(key, columns=["id", "question", "expected_status", "expected_value"]).to_string(index=False))
print("\nrows in orders.csv:", len(orders))
