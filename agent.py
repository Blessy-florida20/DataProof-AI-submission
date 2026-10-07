"""The agent: plan -> write code -> run -> observe -> retry -> independently verify.

Usage:  python agent.py "What is the total revenue in INR across all currencies?"
"""
import glob
import json
import os
import subprocess
import sys

import pandas as pd

from llm import ask

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PROOFS = os.path.join(ROOT, "proofs")
MAX_ATTEMPTS = 3

HEADER = (
    "import os\n"
    'DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")\n\n'
)

SOLVER_SYSTEM = """You are a careful data-analyst agent answering questions about CSV tables.
Return ONLY one JSON object with keys: status, reason, assumptions, data_issues, code.

status must be one of:
- "ANSWER": the data supports one well-defined answer.
- "AMBIGUOUS": the question has 2+ reasonable readings that change the result (for example a date such as
  03/04/2026 that could be day/month or month/day, an unstated currency, an unclear time period).
  Explain each reading in "reason". Do not guess.
- "CANNOT_DETERMINE": required columns or entities do not exist (for example profit with no cost data, or a
  region/product/customer that is not in the data). Say exactly what is missing in "reason".
A confident wrong answer is far worse than refusing. Check distinct values before assuming something exists.

If status is ANSWER, "code" is a complete Python script (pandas + standard library only) that:
- loads files with f"{DATA}/orders.csv" etc. (DATA is already defined, do not redefine it),
- cleans the data: drop exact duplicate rows, exclude rows missing values the calculation needs,
  parse dates carefully, convert all money to INR with fx_rates.csv (rate_to_inr) unless told otherwise,
- ends with exactly one line: print("RESULT:", value)   where value is ONE number (rounded to 2 decimals) or ONE string.
List what you assumed in "assumptions" and what messy data you found in "data_issues".
If status is not ANSWER, set "code" to "".
No markdown, no commentary outside the JSON."""

VERIFIER_SYSTEM = SOLVER_SYSTEM + """

You are the INDEPENDENT VERIFIER. You have not seen any other solution. Solve the question with a
DIFFERENT method than the obvious one (for example load the tables into sqlite3 and use SQL, or loop row by
row). Follow the same output format."""


def schema_summary():
    parts = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        if os.path.basename(f) == "answer_key.csv":  # never show the answers to the model
            continue
        df = pd.read_csv(f)
        name = os.path.basename(f)
        parts.append(f"FILE {name} ({len(df)} rows)\ncolumns: {list(df.columns)}\n"
                     f"sample rows:\n{df.head(5).to_string(index=False)}")
        cats = {c: sorted(df[c].dropna().astype(str).unique().tolist())
                for c in df.columns
                if not pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() <= 10}
        if cats:
            parts.append(f"distinct values (low-cardinality columns): {cats}")
    return "\n\n".join(parts)


def extract_json(text):
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def run_script(path, timeout=30):
    """Run a proof script in a fresh process. Returns (ok, value, output)."""
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True,
                           timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return False, None, "timed out"
    lines = [l for l in p.stdout.splitlines() if l.startswith("RESULT:")]
    if p.returncode != 0 or not lines:
        return False, None, (p.stderr or p.stdout)[-1500:]
    return True, lines[-1].split(":", 1)[1].strip(), p.stdout


def same(a, b):
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) <= 1e-6 * max(1.0, abs(fa), abs(fb))
    except (TypeError, ValueError):
        return str(a).strip().lower() == str(b).strip().lower()


def _write_proof(name, code):
    os.makedirs(PROOFS, exist_ok=True)
    path = os.path.join(PROOFS, name + ".py")
    with open(path, "w") as fh:
        fh.write(HEADER + code.strip() + "\n")
    return path


def answer(question, qid="adhoc"):
    schema = schema_summary()
    steps, feedback = [], ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        user = f"DATA SCHEMA:\n{schema}\n\nQUESTION: {question}\n{feedback}"
        try:
            obj = extract_json(ask(SOLVER_SYSTEM, user, "solver"))
        except Exception as e:  # unparsable model output -> retry
            steps.append(f"Attempt {attempt}: model reply was not valid JSON ({e}); retrying")
            feedback = "Your last reply was not valid JSON. Return ONLY the JSON object."
            continue

        base = {"reason": obj.get("reason", ""), "assumptions": obj.get("assumptions", []),
                "data_issues": obj.get("data_issues", []), "steps": steps, "code": None,
                "proof_path": None, "value": None}

        if obj.get("status") in ("AMBIGUOUS", "CANNOT_DETERMINE"):
            steps.append(f"Attempt {attempt}: agent decided {obj['status']}")
            return {**base, "status": obj["status"]}

        path = _write_proof(f"{qid}", obj.get("code", ""))
        ok, value, out = run_script(path)
        if not ok:
            steps.append(f"Attempt {attempt}: code failed -> asking agent to fix")
            feedback = f"Your previous code failed with this error. Fix it:\n{out}"
            continue
        steps.append(f"Attempt {attempt}: code ran, result = {value}")

        # ---- verification 1: re-run the saved proof in a fresh process (reproducibility)
        ok2, value2, _ = run_script(path)
        reproducible = ok2 and same(value, value2)
        steps.append(f"Verifier 1 (fresh re-run): {'match' if reproducible else 'MISMATCH'}")

        # ---- verification 2: independent second solution by a different method
        indep = None
        try:
            vobj = extract_json(ask(VERIFIER_SYSTEM, f"DATA SCHEMA:\n{schema}\n\nQUESTION: {question}", "verifier"))
            if vobj.get("status") == "ANSWER":
                vpath = _write_proof(f"{qid}_verifier", vobj.get("code", ""))
                okv, vval, _ = run_script(vpath)
                indep = okv and same(value, vval)
                steps.append(f"Verifier 2 (independent method): {vval if okv else 'failed to run'} -> "
                             f"{'match' if indep else 'MISMATCH'}")
            else:
                indep = False
                steps.append(f"Verifier 2 disagreed on feasibility: {vobj.get('status')}")
        except Exception as e:
            indep = False
            steps.append(f"Verifier 2 error: {e}")

        status = "VERIFIED" if (reproducible and indep) else "UNVERIFIED"
        return {**base, "status": status, "value": value, "code": HEADER + obj["code"].strip(),
                "proof_path": path}

    return {"status": "FAILED", "value": None, "reason": "Agent could not produce working code.",
            "assumptions": [], "data_issues": [], "steps": steps, "code": None, "proof_path": None}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the total revenue in INR across all currencies?"
    r = answer(q)
    print(json.dumps({k: v for k, v in r.items() if k != "code"}, indent=2, ensure_ascii=False))
    if r["proof_path"]:
        print("\nProof script saved at:", r["proof_path"])
