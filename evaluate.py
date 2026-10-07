"""Scores the agent against answer_key.csv, like the judges will.
Usage:  python evaluate.py
"""
import pandas as pd

from agent import answer, same

key = pd.read_csv("answer_key.csv", dtype=str, keep_default_na=False)
passed = 0
for _, row in key.iterrows():
    r = answer(row["question"], qid=row["id"])
    exp = row["expected_status"]
    if exp == "ANSWER":
        ok = r["status"] == "VERIFIED" and same(r["value"], row["expected_value"])
    else:
        ok = r["status"] == exp
    passed += ok
    got = r["value"] if r["value"] is not None else r["status"]
    print(f'{"PASS" if ok else "FAIL"}  {row["id"]:<4} expected={exp}:{row["expected_value"]!s:<10} got={r["status"]}:{got}')
print(f"\nScore: {passed}/{len(key)}")
