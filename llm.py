"""One function, ask(system, user, role), that talks to whichever LLM you choose.

Choose with environment variables (nothing is hard-coded, no key in the code):
    LLM_PROVIDER = mock | gemini | openai | anthropic     (default: mock)
    GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
    LLM_MODEL    = optional, overrides the default model name

'mock' needs no key. It only knows a few demo questions so you can test the
pipeline (code execution, verifier, refusals) before you have an API key.
"""
import json
import os
import re

import requests

PROVIDER = os.environ.get("LLM_PROVIDER", "mock").lower()
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}


def ask(system, user, role="solver"):
    model = os.environ.get("LLM_MODEL", DEFAULT_MODELS.get(PROVIDER, ""))
    if PROVIDER == "mock":
        return _mock(user, role)
    if PROVIDER == "gemini":
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            json={"system_instruction": {"parts": [{"text": system}]},
                  "contents": [{"role": "user", "parts": [{"text": user}]}],
                  "generationConfig": {"temperature": 0}},
            timeout=120)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    if PROVIDER == "openai":
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
            json={"model": model, "temperature": 0,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    if PROVIDER == "anthropic":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                     "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 3000, "temperature": 0, "system": system,
                  "messages": [{"role": "user", "content": user}]},
            timeout=120)
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")


# ---------------------------------------------------------------- mock (no key)
_PANDAS_TOTAL = '''import pandas as pd
o = pd.read_csv(f"{DATA}/orders.csv").drop_duplicates()
o = o.dropna(subset=["quantity", "unit_price"])
fx = pd.read_csv(f"{DATA}/fx_rates.csv")
o = o.merge(fx, on="currency")
value = (o["quantity"] * o["unit_price"] * o["rate_to_inr"]).sum()
print("RESULT:", round(float(value), 2))
'''
_SQL_TOTAL = '''import sqlite3
import pandas as pd
con = sqlite3.connect(":memory:")
pd.read_csv(f"{DATA}/orders.csv").drop_duplicates().to_sql("orders", con, index=False)
pd.read_csv(f"{DATA}/fx_rates.csv").to_sql("fx", con, index=False)
v = con.execute("SELECT SUM(o.quantity*o.unit_price*f.rate_to_inr) FROM orders o "
                "JOIN fx f ON o.currency=f.currency "
                "WHERE o.quantity IS NOT NULL AND o.unit_price IS NOT NULL").fetchone()[0]
print("RESULT:", round(float(v), 2))
'''


def _mock(user, role):
    q = re.search(r"QUESTION:\s*(.+)", user).group(1).lower()
    if "profit" in q or "margin" in q:
        return json.dumps({"status": "CANNOT_DETERMINE",
                           "reason": "No cost or profit columns exist in any table, so profit cannot be derived.",
                           "assumptions": [], "data_issues": [], "code": ""})
    if "mars" in q:
        return json.dumps({"status": "CANNOT_DETERMINE",
                           "reason": "Region 'Mars' does not exist. Valid regions: East, North, South, West.",
                           "assumptions": [], "data_issues": [], "code": ""})
    if "03/04/2026" in q:
        return json.dumps({"status": "AMBIGUOUS",
                           "reason": "03/04/2026 could be 3 April 2026 (day/month) or 4 March 2026 (month/day). "
                                     "The answer differs by reading; please specify the format.",
                           "assumptions": [], "data_issues": [], "code": ""})
    if "total revenue in inr across" in q:
        return json.dumps({"status": "ANSWER", "reason": "",
                           "assumptions": ["Revenue = quantity x unit_price, converted to INR with fx_rates.csv"],
                           "data_issues": ["Exact duplicate rows removed", "Rows with missing quantity/price excluded"],
                           "code": _SQL_TOTAL if role == "verifier" else _PANDAS_TOTAL})
    return json.dumps({"status": "CANNOT_DETERMINE",
                       "reason": "Mock mode only knows a few demo questions. Set LLM_PROVIDER to use a real model.",
                       "assumptions": [], "data_issues": [], "code": ""})
