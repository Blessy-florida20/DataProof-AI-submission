import html
import os

import pandas as pd
import streamlit as st

import llm
from agent import DATA, answer, same

# ---------------------------------------------------------------- theme file
THEME = """[theme]
base = "light"
primaryColor = "#14213D"
backgroundColor = "#EDF0F3"
secondaryBackgroundColor = "#E2E7EC"
textColor = "#14213D"
font = "sans serif"

[browser]
gatherUsageStats = false
"""
CFG = os.path.join(".streamlit", "config.toml")
theme_created = False
if not os.path.exists(CFG):
    os.makedirs(".streamlit", exist_ok=True)
    with open(CFG, "w") as fh:
        fh.write(THEME)
    theme_created = True

st.set_page_config(page_title="DataProof AI", page_icon="✅", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=Courier+Prime:wght@400;700&display=swap');
:root{--paper:#EDF0F3;--ink:#14213D;--slip:#FCFCFA;--mark:#FFE066;--green:#0B7A5E;--amber:#B7791F;--red:#C0272D;--muted:#6B7690}
.stApp{background:var(--paper);color:var(--ink);font-family:'Bricolage Grotesque',system-ui,sans-serif}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp li{font-family:'Bricolage Grotesque',system-ui,sans-serif}
section[data-testid="stSidebar"]{background:#E2E7EC}
.block-container{padding-top:2.2rem;max-width:1180px}
.wordmark{font-weight:800;font-size:1.05rem;letter-spacing:-.01em;margin-bottom:1.4rem}
.wordmark span{display:inline-block;background:var(--ink);color:var(--paper);border-radius:6px;padding:.05rem .45rem;margin-right:.4rem}
.headline{font-weight:800;font-size:clamp(2.4rem,4.6vw,3.8rem);line-height:1.02;letter-spacing:-.035em;margin:0 0 .8rem 0}
.lede{font-size:1.1rem;line-height:1.5;max-width:34rem;margin:0 0 1.4rem 0;color:#2b3a5e}
h2.sec{font-weight:800;letter-spacing:-.02em;font-size:1.8rem;margin:2.6rem 0 .3rem 0}
p.sub{color:#2b3a5e;max-width:42rem;margin:0 0 1rem 0}

/* chips and buttons */
div.stButton>button{border:1.5px solid var(--ink);border-radius:6px;background:transparent;color:var(--ink);
  font-family:'Bricolage Grotesque',sans-serif;font-weight:600;padding:.35rem .7rem;transition:background .15s,transform .1s;width:100%}
div.stButton{width:100%}
div.stButton>button:hover{background:var(--mark);border-color:var(--ink);color:var(--ink)}
div.stButton>button:active{transform:translateY(1px)}
div.stButton>button:focus-visible{outline:3px solid var(--mark);outline-offset:2px}
div.stButton>button[kind="primary"],div.stButton>button[data-testid="stBaseButton-primary"]{background:var(--ink);color:var(--paper)}
div.stButton>button[kind="primary"]:hover,div.stButton>button[data-testid="stBaseButton-primary"]:hover{background:#243a6b;color:#fff}
div[data-baseweb="input"]{border-radius:6px}
div[data-baseweb="input"] input{font-family:'Bricolage Grotesque',sans-serif}

/* the slip */
.slip{position:relative;background:var(--slip);padding:1.3rem 1.4rem 1.7rem 1.4rem;border-radius:4px 4px 0 0;
  box-shadow:0 1px 0 rgba(20,33,61,.15),0 12px 24px -14px rgba(20,33,61,.35);font-family:'Courier Prime',monospace;font-size:.95rem}
.slip:after{content:"";position:absolute;left:0;right:0;bottom:-9px;height:9px;
  background:radial-gradient(circle at 7px -2px,transparent 6px,var(--slip) 7px) repeat-x;background-size:14px 9px}
.slip .title{font-weight:700;font-size:1.05rem;margin-bottom:.2rem}
.slip .when{color:var(--muted);font-size:.8rem;margin-bottom:.9rem;border-bottom:2px dashed #c3cad8;padding-bottom:.8rem}
.slip .q{font-family:'Bricolage Grotesque',sans-serif;font-weight:600;font-size:1.02rem;line-height:1.3;margin-bottom:.9rem}
.slip .row{display:flex;gap:.5rem;align-items:baseline;margin:.18rem 0}
.slip .row i{flex:1;border-bottom:2px dotted #9aa5b8;transform:translateY(-3px)}
.slip .ok{color:var(--green);font-weight:700}.slip .no{color:var(--red);font-weight:700}
.slip .total{margin-top:.9rem;padding-top:.8rem;border-top:2px dashed #c3cad8}
.slip .total small{color:var(--muted)}
.slip .result{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:2.7rem;letter-spacing:-.03em;line-height:1.05;margin:.1rem 0 0 0;max-width:62%}
.slip .why{font-family:'Bricolage Grotesque',sans-serif;font-size:1rem;line-height:1.45;margin:.3rem 0 0 0;max-width:68%}
.stamp{position:absolute;right:16px;bottom:22px;padding:.35rem .8rem;border:4px double currentColor;border-radius:8px;
  font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:1.25rem;letter-spacing:.04em;text-transform:uppercase;
  transform:rotate(-9deg);opacity:.92;mix-blend-mode:multiply;animation:thump .42s cubic-bezier(.2,1.4,.4,1) both}
.stamp.green{color:var(--green)}.stamp.amber{color:var(--amber)}.stamp.red{color:var(--red)}.stamp.grey{color:#9aa5b8}
@keyframes thump{0%{transform:rotate(-2deg) scale(1.9);opacity:0}70%{transform:rotate(-10deg) scale(.96);opacity:.95}100%{transform:rotate(-9deg) scale(1)}}
@media (prefers-reduced-motion:reduce){.stamp{animation:none}}

/* notes and tiles */
.note{border-left:5px solid var(--ink);padding:.6rem 1rem;margin:.7rem 0 1rem 0;background:rgba(255,224,102,.35);border-radius:0 6px 6px 0;max-width:46rem}
.note b{font-weight:800}
.tiles{display:flex;flex-wrap:wrap;gap:.5rem;margin:.6rem 0}
.tile{width:62px;text-align:center;padding:.45rem 0;border:2px solid;border-radius:8px;font-weight:800;font-size:.95rem}
.tile small{display:block;font-weight:600;font-size:.7rem}
.tile.p{color:var(--green);background:rgba(11,122,94,.10)}.tile.f{color:var(--red);background:rgba(192,39,45,.10)}
.score{font-weight:800;font-size:3rem;letter-spacing:-.03em;line-height:1}
.dot{display:inline-block;width:.6rem;height:.6rem;border-radius:50%;margin-right:.45rem}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------- data helpers


@st.cache_data
def load_tables():
    return {f[:-4]: pd.read_csv(os.path.join(DATA, f)) for f in sorted(os.listdir(DATA))
            if f.endswith(".csv") and f != "answer_key.csv"}


def trap_defs(t):
    o, pay = t["orders"], t["payments"]
    iso = pd.to_datetime(o["order_date"], format="%Y-%m-%d", errors="coerce").notna()
    parts = o["order_date"].astype(str).str.extract(r"^(\d{2})/(\d{2})/\d{4}$").astype(float)
    amb = (parts[0] <= 12) & (parts[1] <= 12)
    u = o.drop_duplicates().dropna(subset=["quantity", "unit_price"]).merge(pay, on="order_id")
    bad = u.loc[(u["quantity"] * u["unit_price"] - u["amount_paid"]).abs() > 1e-9, "order_id"].tolist()
    return {
        "Duplicates": (o.duplicated(keep=False), int(o.duplicated().sum()),
                       "The same order appears twice. Counting both would inflate revenue.",
                       "Removes exact duplicate rows before any calculation and says how many it removed."),
        "Missing values": (o[["quantity", "unit_price"]].isna().any(axis=1), int(o[["quantity", "unit_price"]].isna().any(axis=1).sum()),
                           "A blank quantity or price means the order value is unknown.",
                           "Leaves those rows out of revenue and reports that it did."),
        "Mixed currencies": (o["currency"] != "INR", int((o["currency"] != "INR").sum()),
                             "Prices are in USD and EUR as well as INR. Adding them directly gives a meaningless total.",
                             "Converts everything to INR with fx_rates.csv and states the rates."),
        "Odd date formats": (~iso, int((~iso).sum()),
                             "Dates come as 2026-01-02, 5 Jan 2026 and 15/02/2026 in the same column.",
                             "Parses each format explicitly instead of trusting one guess."),
        "Ambiguous dates": (amb, int(amb.sum()),
                            "03/04/2026 can be 3 April or 4 March, and both are valid. 15/02/2026 can only be 15 February.",
                            "Refuses to guess. It explains both readings and asks you to pick."),
        "Payments disagree": (o["order_id"].isin(bad), len(bad),
                              "payments.csv records a different amount than the order for: " + ", ".join(bad) + ".",
                              "Reports which source it used when the two tables contradict each other."),
    }


tables = load_tables()
traps = trap_defs(tables)

# ---------------------------------------------------------------- display helpers


def pretty(value, question):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return str(value)
    q = question.lower()
    if "inr" in q or "revenue" in q or "sales" in q:
        whole, dec = f"{abs(x):.2f}".split(".")
        if len(whole) > 3:
            head, tail, grp = whole[:-3], whole[-3:], []
            while len(head) > 2:
                grp.insert(0, head[-2:])
                head = head[:-2]
            if head:
                grp.insert(0, head)
            whole = ",".join(grp + [tail])
        return ("-" if x < 0 else "") + "₹" + whole + ("" if dec == "00" else "." + dec)
    return f"{int(x)}" if x.is_integer() else f"{x:g}"


STAMPS = {"VERIFIED": ("Verified", "green"), "UNVERIFIED": ("Not verified", "red"),
          "AMBIGUOUS": ("Ambiguous", "amber"), "CANNOT_DETERMINE": ("Cannot determine", "red"),
          "FAILED": ("Failed", "red")}


def check_flags(r):
    s = " ".join(r["steps"])
    return ("Verifier 1 (fresh re-run): match" in s, "(independent method)" in s and "-> match" in s)


def receipt(r=None, q=""):
    e = html.escape
    if r is None:  # example slip
        rows = [("Attempts", "1", ""), ("Re-run in a fresh process", "match", "ok"),
                ("Independent method", "match", "ok"), ("Assumptions stated", "2", ""), ("Messy data fixed", "3", "")]
        body = "".join(f'<div class="row"><span>{a}</span><i></i><span class="{c}">{b}</span></div>' for a, b, c in rows)
        return (f'<div class="slip"><div class="title">DataProof audit slip</div>'
                f'<div class="when">Example. Ask a question to get yours.</div>'
                f'<div class="q">What is the total revenue in INR across all currencies?</div>{body}'
                f'<div class="total"><small>Result</small><div class="result">₹5,96,330</div></div>'
                f'<div class="stamp grey">Example</div></div>')
    label, color = STAMPS[r["status"]]
    if r["value"] is not None:
        v1, v2 = check_flags(r)
        attempts = sum(1 for s in r["steps"] if s.startswith("Attempt"))
        rows = [("Attempts", str(attempts), ""),
                ("Re-run in a fresh process", "match" if v1 else "mismatch", "ok" if v1 else "no"),
                ("Independent method", "match" if v2 else "mismatch", "ok" if v2 else "no"),
                ("Assumptions stated", str(len(r["assumptions"])), ""),
                ("Messy data fixed", str(len(r["data_issues"])), "")]
        body = "".join(f'<div class="row"><span>{a}</span><i></i><span class="{c}">{b}</span></div>' for a, b, c in rows)
        total = f'<small>Result</small><div class="result">{e(pretty(r["value"], q))}</div>'
    else:
        body = ""
        reason = r["reason"] or "The agent could not produce working code. Check the steps below, then try rephrasing."
        total = f'<small>Why no number</small><div class="why">{e(reason)}</div>'
    return (f'<div class="slip"><div class="title">DataProof audit slip</div>'
            f'<div class="when">Provider: {e(llm.PROVIDER)}</div>'
            f'<div class="q">{e(q)}</div>{body}<div class="total">{total}</div>'
            f'<div class="stamp {color}">{label}</div></div>')


# ---------------------------------------------------------------- state and run
ss = st.session_state
ss.setdefault("q", "")
ss.setdefault("run", False)
ss.setdefault("last", None)
ss.setdefault("history", [])
ss.setdefault("board", None)


def pick(question):
    ss.q = question
    ss.run = True


def go():
    ss.run = True


error_msg = None
if ss.run and ss.q.strip():
    ss.run = False
    q = ss.q.strip()
    try:
        with st.spinner("Writing code, running it and checking it twice..."):
            res = answer(q, qid="app")
        ss.last = {"q": q, "r": res}
        ss.history.insert(0, ss.last)
    except KeyError as ex:
        error_msg = f"Missing setting {ex}. Set the API key in the same terminal that runs the app, then restart it."
    except Exception as ex:  # network errors, bad model names, etc.
        error_msg = f"The AI request failed: {ex}. Check your key and model name (LLM_MODEL), then try again."
else:
    ss.run = False

with st.sidebar:
    st.markdown("**Setup**")
    st.write(f"AI provider: `{llm.PROVIDER}`")
    if llm.PROVIDER == "mock":
        st.warning("Mock mode. Only four demo questions work. Set LLM_PROVIDER and an API key to use the full agent.")
    st.write(f"Tables loaded: {len(tables)}")
    if theme_created:
        st.info("Theme file created. Stop the app with Ctrl+C and run it again for the full look.")
    if ss.history:
        st.markdown("**Recent questions**")
        for h in ss.history[:8]:
            _, colr = STAMPS[h["r"]["status"]]
            hexes = {"green": "#0B7A5E", "amber": "#B7791F", "red": "#C0272D"}
            st.markdown(f'<span class="dot" style="background:{hexes[colr]}"></span>{html.escape(h["q"])}',
                        unsafe_allow_html=True)

# ---------------------------------------------------------------- hero
st.markdown('<div class="wordmark"><span>✓</span>DataProof</div>', unsafe_allow_html=True)
left, right = st.columns([1.2, 1], gap="large")

with left:
    st.markdown('<div class="headline">Every number comes with receipts.</div>'
                '<p class="lede">Ask a question about your tables. You get the answer, the code behind it, and two '
                'independent checks. If the data cannot support an answer, it says so instead of guessing.</p>',
                unsafe_allow_html=True)
    chips = [("Duplicate rows", "How many duplicate order rows are there?"),
             ("Revenue in ₹", "What is the total revenue in INR across all currencies?"),
             ("Enterprise revenue", "What is the total revenue in INR from Enterprise customers?"),
             ("Top product", "Which product generated the highest revenue in INR?"),
             ("February revenue", "What was the total revenue in INR in February 2026?"),
             ("Payment mismatches", "For how many orders do payments disagree with the order amount?"),
             ("Orders on 03/04/2026", "How many orders were placed on 03/04/2026?"),
             ("Profit margin", "What was the profit margin?"),
             ("Revenue in Mars", "What was the total revenue in the Mars region?")]
    cols = st.columns(3)
    for i, (label, question) in enumerate(chips):
        cols[i % 3].button(label, key=f"chip{i}", on_click=pick, args=(question,))
    st.text_input("Or ask your own question", key="q", on_change=go,
                  placeholder="For example: What was India's revenue in January?")
    st.button("Analyze", type="primary", on_click=go)
    if error_msg:
        st.error(error_msg)

with right:
    last = ss.last
    st.markdown(receipt(last["r"], last["q"]) if last else receipt(), unsafe_allow_html=True)

# ---------------------------------------------------------------- the working
if ss.last:
    r = ss.last["r"]
    st.markdown('<h2 class="sec">The working</h2><p class="sub">Everything behind the number, so you can check it '
                'yourself.</p>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Proof code", "Agent steps", "Assumptions and data issues"])
    with t1:
        if r["code"]:
            st.code(r["code"], language="python")
            st.download_button("Download proof script", r["code"], file_name="proof.py")
            st.caption("This script loads the CSVs itself. Put it in a folder next to `data/` or run the saved copy in `proofs/`.")
        else:
            st.write("No code was produced, because the agent declined to give a number. The reason is on the slip.")
    with t2:
        for s in r["steps"]:
            st.markdown(f"- {s}")
    with t3:
        a, b = st.columns(2)
        a.markdown("**Assumptions**")
        for x in r["assumptions"] or ["None stated."]:
            a.markdown(f"- {x}")
        b.markdown("**Messy data handled**")
        for x in r["data_issues"] or ["None found."]:
            b.markdown(f"- {x}")

# ---------------------------------------------------------------- trap lab
st.markdown('<h2 class="sec">Messy data, marked up</h2><p class="sub">These are the problems planted in the orders '
            'table. Pick one to see the affected rows highlighted and what the agent does about it.</p>',
            unsafe_allow_html=True)
labels = [f"{k} ({v[1]})" for k, v in traps.items()] + ["No profit data", "Region that does not exist"]
choice = st.radio("Problem", labels, horizontal=True, label_visibility="collapsed")
orders = tables["orders"]
if choice.startswith(tuple(traps)):
    name = choice.rsplit(" (", 1)[0]
    mask, _, problem, fix = traps[name]

    def hl(row):
        return ["background-color:#FFE066" if mask.loc[row.name] else "" for _ in row]
    st.dataframe(orders.style.apply(hl, axis=1), height=300)
    st.markdown(f'<div class="note"><b>The problem.</b> {html.escape(problem)}<br><b>What the agent does.</b> '
                f'{html.escape(fix)}</div>', unsafe_allow_html=True)
elif choice == "No profit data":
    cols_by_table = {n: ", ".join(d.columns) for n, d in tables.items()}
    st.table(pd.DataFrame({"table": list(cols_by_table), "columns": list(cols_by_table.values())}))
    st.markdown('<div class="note"><b>The problem.</b> No table has a cost, margin or profit column.<br>'
                '<b>What the agent does.</b> Declines and names what is missing, instead of inventing a number.</div>',
                unsafe_allow_html=True)
else:
    st.dataframe(orders["region"].value_counts().rename_axis("region").reset_index(name="orders"))
    st.markdown('<div class="note"><b>The problem.</b> The regions are East, North, South and West. '
                '"Mars" is not one of them.<br><b>What the agent does.</b> Checks the real values first and says '
                'the region does not exist.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- scoreboard
st.markdown('<h2 class="sec">Test run</h2><p class="sub">Runs all ten questions in answer_key.csv and marks each one '
            'against the correct answer. This is how a judge would test it.</p>', unsafe_allow_html=True)
if st.button("Run all 10 questions"):
    if not os.path.exists("answer_key.csv"):
        st.error("answer_key.csv was not found. Run `python gen_data.py` in the project folder.")
    else:
        key = pd.read_csv("answer_key.csv", dtype=str, keep_default_na=False)
        results, bar = [], st.progress(0.0, text="Starting")
        for i, (_, k) in enumerate(key.iterrows(), 1):
            bar.progress((i - 1) / len(key), text=f'Checking {k["id"]}: {k["question"]}')
            try:
                rr = answer(k["question"], qid=k["id"])
                ok = (rr["status"] == "VERIFIED" and same(rr["value"], k["expected_value"])) \
                    if k["expected_status"] == "ANSWER" else rr["status"] == k["expected_status"]
            except Exception:
                ok = False
            results.append((k["id"], k["question"], ok))
        bar.empty()
        ss.board = results
if ss.board:
    passed = sum(1 for _, _, ok in ss.board if ok)
    tiles = "".join(f'<div class="tile {"p" if ok else "f"}" title="{html.escape(qq)}">{i}<small>{"pass" if ok else "fail"}</small></div>'
                    for i, qq, ok in ss.board)
    st.markdown(f'<div class="score">{passed} of {len(ss.board)} passed</div><div class="tiles">{tiles}</div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- how it works
with st.expander("How an answer is made"):
    st.graphviz_chart('''digraph G{rankdir=LR;bgcolor="transparent";
node[shape=box,style="rounded,filled",fontname="Helvetica",color="#14213D",fillcolor="#FCFCFA",fontcolor="#14213D"];
edge[color="#14213D",fontname="Helvetica",fontsize=10,fontcolor="#14213D"];
Q[label="Your question"];S[label="Table columns\\nand sample rows"];L[label="AI writes\\nPython code"];
R[label="Run in a fresh\\nprocess"];V1[label="Re-run and\\ncompare"];V2[label="Second solution,\\ndifferent method"];
OK[label="Verified",fillcolor="#b7e4d6"];NO[label="Not verified",fillcolor="#f3c1c3"];X[label="Cannot determine\\nor ambiguous",fillcolor="#f3dfae"];
Q->S->L;L->R[label="has an answer"];L->X[label="data cannot\\nsupport it"];R->L[label="error: fix and retry",style=dashed];
R->V1->V2;V2->OK[label="numbers match"];V2->NO[label="numbers differ"];}''')
