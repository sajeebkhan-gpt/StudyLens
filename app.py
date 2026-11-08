"""StudyLens - RAG Study Assistant (v6, glassmorphic hero).

v6: animated glassmorphic hero banner (aurora orb, live pulse badge,
shimmer headline), equal-height feature cards with hover lift.
Layout: sidebar (~320px) + main workspace, per Sajeeb's diagram.
Run: streamlit run app.py
"""
import os

import streamlit as st
from pypdf import PdfReader

from rag import (
    Retriever,
    build_study_pack_pdf,
    extractive_answer,
    make_flashcards,
    make_mcq_quiz,
    make_practice_questions,
    split_by_topic,
    summarise,
)

SAMPLE_PDF = os.path.join(os.path.dirname(__file__), "sample", "Software-Engineering-Answers.pdf")

st.set_page_config(
    page_title="StudyLens — RAG Study Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
.stApp { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1100px; }
/* Sidebar */
section[data-testid="stSidebar"] { width: 320px !important; }
section[data-testid="stSidebar"] > div { background: #0f172a; }
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] li { color: #e2e8f0 !important; }
.side-title { font-size: 1.4rem; font-weight: 800; color: #fff; }
.side-sub { color: #94a3b8; font-size: .88rem; margin-bottom: 12px; }
.side-head { font-size: .8rem; font-weight: 800; letter-spacing: .08em; color: #a5b4fc; margin: 18px 0 8px 0; }
.side-stat { font-size: .9rem; color: #cbd5e1; line-height: 1.7; }
.privacy {
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 12px 14px; font-size: .85rem; color: #cbd5e1; margin-top: 18px;
}
/* ---- Hero: animated glassmorphic banner ---- */
@keyframes auroraGlow {
    0% { transform: rotate(0deg) scale(1); opacity: .7; }
    50% { transform: rotate(180deg) scale(1.25); opacity: 1; }
    100% { transform: rotate(360deg) scale(1); opacity: .7; }
}
@keyframes livePulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, .55); }
    70% { box-shadow: 0 0 0 9px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
@keyframes textShimmer {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.banner {
    position: relative; overflow: hidden;
    background: rgba(20, 24, 43, 0.75);
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 20px; padding: 32px 26px; color: white;
    box-shadow: 0 12px 35px -10px rgba(139, 92, 246, 0.25);
    margin-bottom: 16px;
}
.banner .aurora-orb {
    position: absolute; top: -60px; right: -40px; width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(168, 85, 247, .45) 0%, rgba(59, 130, 246, .25) 45%, transparent 70%);
    filter: blur(30px); animation: auroraGlow 12s ease-in-out infinite; pointer-events: none;
}
.banner .hero-content { position: relative; z-index: 1; }
.banner .badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 999px; padding: 6px 14px;
    font-size: .78rem; font-weight: 700; letter-spacing: .08em; color: #e9d5ff;
}
.banner .live-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #10b981; animation: livePulse 2s infinite;
}
.banner h1 {
    font-size: 29px; font-weight: 800; margin: 14px 0 8px 0; line-height: 1.25;
    background: linear-gradient(90deg, #ffffff, #ddd6fe, #60a5fa, #a855f7, #ffffff);
    background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
    animation: textShimmer 6s ease-in-out infinite;
}
.banner .subtitle { color: #94a3b8; font-size: 14px; line-height: 1.5; margin: 0; }
.banner .kicker { font-size: .78rem; font-weight: 700; letter-spacing: .1em; color: #c4b5fd; }
/* ---- Feature cards: equal height, hover lift ---- */
.feature-card {
    display: flex; flex-direction: column; justify-content: space-between;
    height: 100%; min-height: 240px;
    background: #1e293b; color: #f1f5f9; border: 1px solid #334155;
    border-radius: 16px; padding: 20px 22px; margin: 12px 0;
    box-shadow: 0 4px 16px rgba(0,0,0,.25);
    transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
}
.feature-card:hover {
    transform: translateY(-4px);
    border-color: rgba(168, 85, 247, 0.6);
    box-shadow: 0 12px 28px rgba(139, 92, 246, .3);
}
.feature-card h3 { margin-top: 0; color: #fff; }
.feature-card p { color: #e2e8f0; }
.mini-chip {
    background: rgba(0, 0, 0, 0.3); border-left: 3px solid #a855f7;
    border-radius: 0 8px 8px 0; padding: 10px 12px; margin-top: 12px;
    font-size: .9rem; color: #e2e8f0;
}
/* Cards */
.card { background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 16px; padding: 20px 22px; margin: 12px 0; box-shadow: 0 4px 16px rgba(0,0,0,.25); }
.card h3 { margin-top: 0; color: #fff; }
.card p, .card div { color: #e2e8f0; }
.stat { text-align: center; padding: 16px 8px; }
.stat .num { font-size: 1.8rem; font-weight: 800; color: #a5b4fc; }
.stat .lbl { font-size: .85rem; font-weight: 600; color: #cbd5e1; }
.flashcard {
    background: #1e293b; border: 1px solid #334155; border-left: 5px solid #818cf8;
    border-radius: 16px; padding: 26px 28px; margin: 14px 0; min-height: 180px;
}
.flashcard .topic { font-size: .8rem; font-weight: 800; letter-spacing: .08em; color: #a5b4fc; }
.flashcard .q { font-size: 1.25rem; font-weight: 700; color: #fff; margin: 10px 0; }
.flashcard .a { font-size: 1.05rem; color: #e2e8f0; margin-top: 12px; border-top: 1px solid #334155; padding-top: 12px; }
.answer-card { background: linear-gradient(180deg, #eef2ff, #f5f3ff); border: 1px solid #ddd6fe; border-radius: 16px; padding: 20px 22px; margin: 12px 0; color: #1e1b4b; }
.answer-card p { color: #1e1b4b; }
.source-card { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-left: 4px solid #818cf8; border-radius: 12px; padding: 14px 16px; margin: 10px 0; }
.source-card .meta { font-size: .82rem; font-weight: 700; color: #a5b4fc; margin-bottom: 6px; }
.stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; border-radius: 999px; padding: .55rem 1.2rem; font-weight: 700; box-shadow: 0 6px 16px rgba(99,102,241,.35); }
.stButton > button:hover { filter: brightness(1.08); color: white; }
section[data-testid="stFileUploader"] { border: 2px dashed #a5b4fc; border-radius: 16px; padding: 14px; background: rgba(99,102,241,.08); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---- Session state ----
for k, v in {
    "chat_history": [], "mode": "flashcards", "flash_idx": 0,
    "flash_flipped": False, "doc": None, "use_sample": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def load_doc(pdf_file, name):
    with st.spinner("📖 Reading your PDF..."):
        reader = PdfReader(pdf_file)
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((i, text))
    if not pages:
        return None
    with st.spinner("🔍 Building your study index..."):
        chunks = split_by_topic(pages)
        retriever = Retriever(chunks)
    topics = sorted({c.get("topic", "") for c in chunks if c.get("topic")})
    return {"name": name, "pages": pages, "chunks": chunks,
            "retriever": retriever, "topics": topics}


def clear_all():
    st.session_state.doc = None
    st.session_state.chat_history = []
    st.session_state.flash_idx = 0
    st.session_state.flash_flipped = False
    st.session_state.mode = "flashcards"
    st.session_state.use_sample = False


# ================= SIDEBAR =================
with st.sidebar:
    st.markdown('<div class="side-title">🔍 StudyLens v1.0</div><div class="side-sub">Grounded RAG Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-head">📂 DOCUMENT INGESTION</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drag & drop PDF notes here", type=["pdf"])
    if st.button("✨ Load Sample", key="sample_btn"):
        st.session_state.use_sample = True

    if uploaded is not None:
        st.session_state.use_sample = False
        doc = load_doc(uploaded, uploaded.name)
        if doc:
            st.session_state.doc = doc
        else:
            st.warning("No readable text in this PDF.")
    elif st.session_state.use_sample and st.session_state.doc is None:
        if os.path.exists(SAMPLE_PDF):
            doc = load_doc(open(SAMPLE_PDF, "rb"), "Software-Engineering-Answers.pdf (sample)")
            if doc:
                st.session_state.doc = doc

    doc = st.session_state.doc
    st.markdown('<div class="side-head">📊 ACTIVE DOCUMENT STATS</div>', unsafe_allow_html=True)
    if doc:
        st.markdown(
            f'<div class="side-stat">• File: {doc["name"]}<br>'
            f'• Pages: {len(doc["pages"])} &nbsp;|&nbsp; Chunks: {len(doc["chunks"])}<br>'
            f'• Topics: {len(doc["topics"])}<br>• Processing: Ready ✅</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="side-stat">• No document loaded yet.<br>• Upload a PDF, or load the sample.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-head">⚙️ WORKSPACE CONTROLS</div>', unsafe_allow_html=True)
    if doc:
        if st.button("⬇️ Download Revision Pack", key="dl_pack_side"):
            with st.spinner("📦 Building your revision pack..."):
                pdf_bytes = build_study_pack_pdf(doc["chunks"])
            st.download_button(
                "📥 Download StudyLens-Study-Pack.pdf",
                data=pdf_bytes, file_name="StudyLens-Study-Pack.pdf",
                mime="application/pdf", key="dl_pack_btn",
            )
    if st.button("🔄 Clear & Start Fresh", key="clear_btn"):
        clear_all()
        st.rerun()

    st.markdown(
        '<div class="privacy">🛡️ <b>PRIVACY SHIELD</b><br>'
        'Processed in-memory. Zero server storage. Completely free.</div>',
        unsafe_allow_html=True,
    )

# ================= MAIN WORKSPACE =================
if doc:
    short_name = doc["name"].replace(" (sample)", "").replace(".pdf", "")
    st.markdown(
        f'<div class="banner"><div class="aurora-orb"></div><div class="hero-content">'
        f'<span class="badge"><span class="live-dot"></span>RAG GROUNDED • IN-MEMORY VECTOR SEARCH • FREE</span>'
        f'<h1>🔍 StudyLens — Active Study Deck &amp; Knowledge Engine</h1>'
        f'<p class="subtitle">{short_name} is active — {len(doc["pages"])} pages indexed. Ask, summarise, quiz yourself; every answer comes from your document, with the source shown.</p>'
        f'<div class="kicker" style="margin-top:10px">✦ {short_name.upper()} ACTIVE • {len(doc["pages"])} PAGES INDEXED</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="card stat"><div class="num">📄 {len(doc["pages"])}</div><div class="lbl">Pages</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card stat"><div class="num">🧩 {len(doc["chunks"])}</div><div class="lbl">Chunks</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card stat"><div class="num">🏷️ {len(doc["topics"])}</div><div class="lbl">Topics</div></div>', unsafe_allow_html=True)

    # Mode buttons
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if st.button("🗂️ Flashcards", key="mode_cards"):
            st.session_state.mode = "flashcards"
    with m2:
        if st.button("💬 Ask PDF", key="mode_ask"):
            st.session_state.mode = "ask"
    with m3:
        if st.button("📝 Summary", key="mode_summary"):
            st.session_state.mode = "summary"
    with m4:
        if st.button("✅ Quiz", key="mode_quiz"):
            st.session_state.mode = "quiz"
    st.divider()

    mode = st.session_state.mode
    chunks = doc["chunks"]
    retriever = doc["retriever"]

    if mode == "flashcards":
        cards = make_flashcards(chunks, n=20)
        if not cards:
            st.write("Not enough topics found in this PDF to build flashcards.")
        else:
            idx = st.session_state.flash_idx % len(cards)
            card = cards[idx]
            st.markdown(f"### 🗂️ CARD {idx + 1} OF {len(cards)}: {card['term'].upper()}")
            answer_html = f'<div class="a">↳ "{card["definition"]}"</div>' if st.session_state.flash_flipped else ""
            st.markdown(
                f'<div class="flashcard"><div class="topic">🏷️ TOPIC: {card["term"].upper()} &nbsp;&nbsp; 📍 Source: Page {card["page"]}</div>'
                f'<div class="q">💡 What is {card["term"]}?</div>'
                f'<div style="color:#94a3b8">Tap Flip Answer to reveal the definition.</div>{answer_html}</div>',
                unsafe_allow_html=True,
            )
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("◀ Prev", key="prev_card"):
                    st.session_state.flash_idx = (idx - 1) % len(cards)
                    st.session_state.flash_flipped = False
                    st.rerun()
            with b2:
                if st.button("🔄 Flip Answer", key="flip_card"):
                    st.session_state.flash_flipped = not st.session_state.flash_flipped
                    st.rerun()
            with b3:
                if st.button("Next ▶", key="next_card"):
                    st.session_state.flash_idx = (idx + 1) % len(cards)
                    st.session_state.flash_flipped = False
                    st.rerun()

    elif mode == "ask":
        for role, text, sources in st.session_state.chat_history:
            with st.chat_message(role):
                st.write(text)
                if sources:
                    for s in sources:
                        st.caption(f"📄 Page {s['page']} • {s.get('topic', '')} • score {s['score']:.2f}")
        question = st.chat_input("Ask a question about this PDF… e.g. What is cyclomatic complexity?")
        if question:
            st.session_state.chat_history.append(("user", question, []))
            with st.chat_message("user"):
                st.write(question)
            with st.spinner("🔍 Searching your PDF for the answer..."):
                retrieved = retriever.retrieve(question, top_k=3)
                answer = extractive_answer(question, retrieved, retriever)
            st.session_state.chat_history.append(("assistant", answer, retrieved))
            with st.chat_message("assistant"):
                st.markdown(f'<div class="answer-card"><p>{answer}</p></div>', unsafe_allow_html=True)
                if retrieved:
                    st.markdown("**📚 Sources**")
                    for r in retrieved:
                        st.markdown(
                            f'<div class="source-card"><div class="meta">Page {r["page"]} • {r.get("topic", "")} • score {r["score"]:.2f}</div>'
                            f'<div>{r["text"][:600]}</div></div>',
                            unsafe_allow_html=True,
                        )
        if st.session_state.chat_history and st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    elif mode == "summary":
        if st.button("✨ Summarise this PDF", key="summarise_btn"):
            with st.spinner("📝 Writing your summary..."):
                summary, key_points = summarise(chunks)
            st.markdown('<div class="card"><h3>📝 Summary</h3><p>' +
                        (summary or "Could not build a summary from this PDF.") +
                        '</p></div>', unsafe_allow_html=True)
            st.markdown("### 🔑 Key points")
            for topic, point in key_points:
                st.markdown(f'<div class="source-card"><div class="meta">{topic}</div><div>{point}</div></div>', unsafe_allow_html=True)

    elif mode == "quiz":
        with st.spinner("✅ Building your quiz..."):
            quiz = make_mcq_quiz(chunks, n=5)
        if not quiz:
            st.write("Not enough definition sentences were found in this PDF to build an MCQ quiz.")
        else:
            for idx, q in enumerate(quiz, start=1):
                st.markdown(f'<div class="card"><h3>Q{idx}. {q["question"]}</h3><p>Page {q["page"]}</p></div>', unsafe_allow_html=True)
                choice = st.radio(f"Choose an answer for Q{idx}", q["options"], key=f"quiz_{idx}")
                if st.button(f"Check Q{idx}", key=f"check_{idx}"):
                    if choice == q["options"][q["answer_index"]]:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"Not quite. Correct answer: {q['options'][q['answer_index']]}")
        st.markdown("### 🎯 Practice Questions")
        if st.button("🎯 Generate practice questions", key="practice_btn"):
            with st.spinner("🎯 Writing practice questions..."):
                practice = make_practice_questions(chunks, n=8)
            for q in practice:
                st.markdown(f'<div class="source-card"><div>{q}</div></div>', unsafe_allow_html=True)
else:
    # Landing page (no document yet)
    st.markdown(
        '<div class="banner"><div class="aurora-orb"></div><div class="hero-content">'
        '<span class="badge"><span class="live-dot"></span>RAG GROUNDED • IN-MEMORY VECTOR SEARCH • FREE</span>'
        '<h1>🔍 StudyLens — Active Study Deck &amp; Knowledge Engine</h1>'
        '<p class="subtitle">Upload your notes. Ask, summarise, quiz yourself — every answer comes from your document, with the source shown. No API key needed, free to use.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### ✨ What you can do with StudyLens")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        st.markdown('<div class="feature-card"><div><h3>💬 Ask from your PDF</h3><p>Ask in plain English, get an answer from your notes — with the page shown.</p></div><div class="mini-chip"><b>Q:</b> What is cyclomatic complexity?<br><b>A:</b> A measure of how complex a program\'s control flow is… <i>(Page 6)</i></div></div>', unsafe_allow_html=True)
    with lc2:
        st.markdown('<div class="feature-card"><div><h3>📝 Summarise in seconds</h3><p>Turn a whole chapter into a short summary and key points for revision.</p></div><div class="mini-chip"><b>Summary:</b> A structural model shows the static structure of a system…</div></div>', unsafe_allow_html=True)
    with lc3:
        st.markdown('<div class="feature-card"><div><h3>✅ Quiz yourself</h3><p>MCQs, practice questions and flashcards — all made from your PDF.</p></div><div class="mini-chip"><b>Q:</b> What is a structural model?<br><b>A.</b> … <b>B.</b> … <b>C.</b> …</div></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card"><h3>👋 How it works</h3>'
        '<p><b>1.</b> Upload a PDF in the sidebar, or load the sample &nbsp;→&nbsp; <b>2.</b> Ask a question, get a summary, or take a quiz &nbsp;→&nbsp; <b>3.</b> Every answer shows its source page.</p>'
        '<p>No file is stored on a server — it is processed in your session. No API key needed, free to use.</p></div>',
        unsafe_allow_html=True,
    )
