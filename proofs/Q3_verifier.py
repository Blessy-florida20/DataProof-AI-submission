import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

import sqlite3
import pandas as pd
con = sqlite3.connect(":memory:")
pd.read_csv(f"{DATA}/orders.csv").drop_duplicates().to_sql("orders", con, index=False)
pd.read_csv(f"{DATA}/fx_rates.csv").to_sql("fx", con, index=False)
v = con.execute("SELECT SUM(o.quantity*o.unit_price*f.rate_to_inr) FROM orders o "
                "JOIN fx f ON o.currency=f.currency "
                "WHERE o.quantity IS NOT NULL AND o.unit_price IS NOT NULL").fetchone()[0]
print("RESULT:", round(float(v), 2))
