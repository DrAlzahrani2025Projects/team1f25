import json, statistics, streamlit as st
from app.rag.retriever import Retriever
from app.rag.hybrid import hybrid_rank

def render_eval_tab():
    st.subheader("Eval — Retrieval (P@k / Recall@k / MRR)")
    k = st.slider("k", 5, 20, 10, 1)
    alpha = st.slider("Hybrid α", 0.0, 1.0, 0.7, 0.05)

    data = []
    try:
        with open("/app/eval/qas.jsonl", "r", encoding="utf-8") as f:
            data = [json.loads(x) for x in f if x.strip()]
    except Exception:
        st.warning("Add some QA to /app/eval/qas.jsonl"); return

    r = Retriever(top_k=max(20,k))
    P, R, RR = [], [], []
    rows = []
    for qa in data:
        q = qa["q"]
        gold_titles = {t.lower().strip() for t in qa.get("titles", [])}
        gold_ids = set(qa.get("record_ids", []))

        dense_hits = r.query(q)
        ranked = hybrid_rank(dense_hits, q, alpha=alpha)
        top = ranked[:k]

        hits_titles = [ (h.get("meta",{}).get("title") or "").lower().strip() for h in top ]
        hits_ids = [ h.get("meta",{}).get("record_id") for h in top ]

        # find any match by id or title
        found_positions = []
        for idx,(t,i) in enumerate(zip(hits_titles, hits_ids), start=1):
            if (t and t in gold_titles) or (i and i in gold_ids):
                found_positions.append(idx)

        p = 1.0 if found_positions else 0.0
        rcl = 1.0 if found_positions else 0.0  # single-answer QA
        rr = 1.0/found_positions[0] if found_positions else 0.0

        P.append(p); R.append(rcl); RR.append(rr)
        rows.append((q, p, rcl, rr, hits_titles[:3]))

    st.table([{"q": q, "P@k": p, "R@k": r, "MRR": rr, "top3": tops} for q,p,r,rr,tops in rows])
    st.success(f"Avg — P@{k}: {statistics.mean(P):.2f} | R@{k}: {statistics.mean(R):.2f} | MRR: {statistics.mean(RR):.2f}")
