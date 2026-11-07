"""StudyLens - RAG Study Assistant (v2).

Upload a PDF, then: ask questions with sources, summarise it,
take an MCQ quiz, or generate exam-style practice questions.
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


st.set_page_config(page_title="StudyLens - RAG Study Assistant", layout="wide")
st.title("StudyLens - RAG Study Assistant")
st.write("Upload your notes as a PDF, ask a question, summarise it, or make a quiz — all grounded in that PDF, with sources shown.")

uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

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
        st.success(f"Loaded {len(pages)} page(s) with readable text.")
        chunks = split_by_topic(pages)
        retriever = Retriever(chunks)

        tab_ask, tab_summary, tab_quiz, tab_practice, tab_cards = st.tabs(
            ["Ask", "Summarise", "Quiz", "Practice Questions", "Flashcards"]
        )

        with tab_ask:
            question = st.text_input("Ask a question about this PDF")
            if question:
                retrieved = retriever.retrieve(question, top_k=3)
                st.subheader("Answer")
                st.write(extractive_answer(question, retrieved, retriever))
                st.subheader("Sources")
                if retrieved:
                    for r in retrieved:
                        st.markdown(f"**Page {r['page']} — {r.get('topic', '')}** (score {r['score']:.2f})")
                        st.write(r["text"][:800])
                else:
                    st.write("No matching passage found in this document.")

        with tab_summary:
            if st.button("Summarise this PDF"):
                summary, key_points = summarise(chunks)
                st.subheader("Summary")
                st.write(summary or "Could not build a summary from this PDF.")
                st.subheader("Key points")
                for topic, point in key_points:
                    st.markdown(f"- **{topic}:** {point}")

        with tab_quiz:
            quiz = make_mcq_quiz(chunks, n=5)
            if not quiz:
                st.write("Not enough definition sentences were found in this PDF to build an MCQ quiz. Try a PDF with more 'X is ...' definitions.")
            else:
                for idx, q in enumerate(quiz, start=1):
                    st.markdown(f"**Q{idx}. {q['question']}**  (Page {q['page']})")
                    choice = st.radio(f"Choose an answer for Q{idx}", q["options"], key=f"quiz_{idx}")
                    if st.button(f"Check Q{idx}", key=f"check_{idx}"):
                        if choice == q["options"][q["answer_index"]]:
                            st.success("Correct!")
                        else:
                            st.error(f"Not quite. Correct answer: {q['options'][q['answer_index']]}")

        with tab_practice:
            if st.button("Generate practice questions"):
                for q in make_practice_questions(chunks, n=8):
                    st.markdown(f"- {q}")

        with tab_cards:
            cards = make_flashcards(chunks, n=8)
            if not cards:
                st.write("Not enough topics found in this PDF to build flashcards.")
            else:
                for idx, card in enumerate(cards, start=1):
                    st.markdown(f"**Card {idx}: {card['term']}**  (Page {card['page']})")
                    if st.button(f"Show definition — Card {idx}", key=f"card_{idx}"):
                        st.write(card["definition"])
else:
    st.info("Start by uploading a PDF above. No file is stored on a server in this v1 demo - it is processed in your session.")
