"""StudyLens - RAG Study Assistant (v3, modern UI).

Upload a PDF, then: ask questions with sources, summarise it,
take an MCQ quiz, generate exam-style practice questions, or
study with flashcards.
Run: streamlit run app.py
"""
import streamlit as st
from pypdf import PdfReader

from rag import (
    Retriever,
    extractive_answer,
    make_flashcards,
    make_mcq_quiz,
    make_practice_questions,
    split_by_topic,
    summarise,
)

st.set_page_config(
    page_title="StudyLens — RAG Study Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODERN_CSS = """
<style>
/* ---- Base ---- */
.stApp { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 980px; }

/* ---- Hero ---- */
.hero {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #ec4899 100%);
    border-radius: 20px; padding: 28px 32px; color: white;
    box-shadow: 0 12px 32px rgba(99,102,241,.35); margin-bottom: 8px;
}
.hero h1 { font-size: 2.2rem; margin: 0; color: white; letter-spacing: -.02em; }
.hero p { font-size: 1.05rem; opacity: .92; margin: 8px 0 0 0; }
.hero .badge {
    display: inline-block; background: rgba(255,255,255,.22);
    border: 1px solid rgba(255,255,255,.35); border-radius: 999px;
    padding: 4px 12px; font-size: .8rem; font-weight: 600; margin-bottom: 10px;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 4px 0; }
.chip {
    background: #eef2ff; color: #4338ca; border: 1px solid #e0e7ff;
    border-radius: 999px; padding: 6px 14px; font-size: .85rem; font-weight: 600;
}
@media (prefers-color-scheme: dark) {
    .chip { background: #1e1b4b; color: #c7d2fe; border-color: #3730a3; }
}

/* ---- Cards ---- */
.card {
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(128,128,128,.25); border-radius: 16px;
    padding: 20px 22px; margin: 12px 0;
    box-shadow: 0 4px 16px rgba(0,0,0,.06);
}
.card h3 { margin-top: 0; }
.answer-card {
    background: linear-gradient(180deg, #eef2ff, #f5f3ff);
    border: 1px solid #ddd6fe; border-radius: 16px; padding: 20px 22px;
    margin: 12px 0; color: #1e1b4b;
}
.source-card {
    border: 1px solid rgba(128,128,128,.25); border-left: 4px solid #6366f1;
    border-radius: 12px; padding: 14px 16px; margin: 10px 0;
}
.source-card .meta { font-size: .82rem; font-weight: 700; color: #6366f1; margin-bottom: 6px; }
.stat { text-align: center; padding: 14px 8px; }
.stat .num { font-size: 1.6rem; font-weight: 800; color: #6366f1; }
.stat .lbl { font-size: .82rem; opacity: .75; }

/* ---- Buttons / inputs ---- */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; border: none; border-radius: 999px;
    padding: .55rem 1.4rem; font-weight: 700;
    box-shadow: 0 6px 16px rgba(99,102,241,.35);
}
.stButton > button:hover { filter: brightness(1.08); color: white; }
.stTextInput input, .stSelectbox select { border-radius: 12px !important; }
section[data-testid="stFileUploader"] {
    border: 2px dashed #a5b4fc; border-radius: 16px; padding: 18px;
    background: rgba(99,102,241,.05);
}
/* Tabs */
button[data-baseweb="tab"] { font-weight: 700; font-size: .95rem; }
</style>
"""

st.markdown(MODERN_CSS, unsafe_allow_html=True)

# ---- Hero ----
st.markdown(
    """
    <div class="hero">
        <span class="badge">✦ RAG • GROUNDED IN YOUR PDF • FREE</span>
        <h1>🔍 StudyLens</h1>
        <p>Upload your notes. Ask, summarise, quiz yourself — every answer comes
        from your document, with the source shown.</p>
    </div>
    <div class="chips">
        <span class="chip">💬 Ask from PDF</span>
        <span class="chip">📝 Summarise</span>
        <span class="chip">✅ MCQ Quiz</span>
        <span class="chip">🎯 Practice Questions</span>
        <span class="chip">🗂️ Flashcards</span>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Upload your notes as a PDF", type=["pdf"])

if uploaded is not None:
    reader = PdfReader(uploaded)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))

    if not pages:
        st.warning("No readable text was found in this PDF. Try a text-based PDF, not a scanned image.")
    else:
        chunks = split_by_topic(pages)
        retriever = Retriever(chunks)
        topics = sorted({c.get("topic", "") for c in chunks if c.get("topic")})

        # ---- Stats row ----
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card stat"><div class="num">{len(pages)}</div><div class="lbl">Pages</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card stat"><div class="num">{len(chunks)}</div><div class="lbl">Topic chunks</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card stat"><div class="num">{len(topics)}</div><div class="lbl">Topics</div></div>', unsafe_allow_html=True)
        st.success(f"✅ Loaded **{uploaded.name}** — {len(pages)} page(s) with readable text.")

        tab_ask, tab_summary, tab_quiz, tab_practice, tab_cards = st.tabs(
            ["💬 Ask", "📝 Summarise", "✅ Quiz", "🎯 Practice", "🗂️ Flashcards"]
        )

        with tab_ask:
            question = st.text_input("Ask a question about this PDF", placeholder="e.g. What is cyclomatic complexity?")
            if question:
                retrieved = retriever.retrieve(question, top_k=3)
                st.markdown('<div class="answer-card"><h3>💡 Answer</h3><p>' +
                            extractive_answer(question, retrieved, retriever) +
                            '</p></div>', unsafe_allow_html=True)
                st.markdown("### 📚 Sources")
                if retrieved:
                    for r in retrieved:
                        st.markdown(
                            f'<div class="source-card"><div class="meta">Page {r["page"]} • {r.get("topic", "")} • score {r["score"]:.2f}</div>'
                            f'<div>{r["text"][:600]}</div></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.write("No matching passage found in this document.")

        with tab_summary:
            if st.button("✨ Summarise this PDF", key="summarise_btn"):
                summary, key_points = summarise(chunks)
                st.markdown('<div class="card"><h3>📝 Summary</h3><p>' +
                            (summary or "Could not build a summary from this PDF.") +
                            '</p></div>', unsafe_allow_html=True)
                st.markdown("### 🔑 Key points")
                for topic, point in key_points:
                    st.markdown(f'<div class="source-card"><div class="meta">{topic}</div><div>{point}</div></div>', unsafe_allow_html=True)

        with tab_quiz:
            quiz = make_mcq_quiz(chunks, n=5)
            if not quiz:
                st.write("Not enough definition sentences were found in this PDF to build an MCQ quiz. Try a PDF with more 'X is ...' definitions.")
            else:
                for idx, q in enumerate(quiz, start=1):
                    st.markdown(f'<div class="card"><h3>Q{idx}. {q["question"]}</h3><p style="opacity:.7">Page {q["page"]}</p></div>', unsafe_allow_html=True)
                    choice = st.radio(f"Choose an answer for Q{idx}", q["options"], key=f"quiz_{idx}")
                    if st.button(f"Check Q{idx}", key=f"check_{idx}"):
                        if choice == q["options"][q["answer_index"]]:
                            st.success("✅ Correct!")
                        else:
                            st.error(f"Not quite. Correct answer: {q['options'][q['answer_index']]}")

        with tab_practice:
            if st.button("🎯 Generate practice questions", key="practice_btn"):
                for q in make_practice_questions(chunks, n=8):
                    st.markdown(f'<div class="source-card"><div>{q}</div></div>', unsafe_allow_html=True)

        with tab_cards:
            cards = make_flashcards(chunks, n=8)
            if not cards:
                st.write("Not enough topics found in this PDF to build flashcards.")
            else:
                for idx, card in enumerate(cards, start=1):
                    st.markdown(f'<div class="card"><h3>🗂️ Card {idx}: {card["term"]}</h3><p style="opacity:.7">Page {card["page"]}</p></div>', unsafe_allow_html=True)
                    if st.button(f"Show definition — Card {idx}", key=f"card_{idx}"):
                        st.write(card["definition"])
else:
    st.markdown(
        """
        <div class="card">
            <h3>👋 How it works</h3>
            <p><b>1.</b> Upload a PDF of your notes &nbsp;→&nbsp; <b>2.</b> Ask a question, get a summary, or take a quiz &nbsp;→&nbsp; <b>3.</b> Every answer shows its source page.</p>
            <p style="opacity:.75">No file is stored on a server — it is processed in your session. No API key needed, free to use.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
