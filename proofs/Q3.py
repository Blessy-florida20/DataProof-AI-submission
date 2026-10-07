import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

import pandas as pd
o = pd.read_csv(f"{DATA}/orders.csv").drop_duplicates()
o = o.dropna(subset=["quantity", "unit_price"])
fx = pd.read_csv(f"{DATA}/fx_rates.csv")
o = o.merge(fx, on="currency")
value = (o["quantity"] * o["unit_price"] * o["rate_to_inr"]).sum()
print("RESULT:", round(float(value), 2))
