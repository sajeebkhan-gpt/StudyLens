# StudyLens — RAG Study Assistant

A study-friendly Retrieval-Augmented Generation (RAG) assistant built by Sajeeb Khan.

Upload your own class notes as a PDF, and StudyLens helps you study from it —
not just by answering questions, but by summarising it, making a quiz, and
generating practice questions like an exam.

**Status: skeleton ready, not yet deployed.** The live link will be added here
only after deployment on Streamlit Cloud / Hugging Face Spaces is tested and works.

This is a separate project from StudyMate AI (the React Native / FastAPI
learning-platform app on Sajeeb's resume). StudyLens is a new, standalone
Streamlit web app.

## Main features
1. **Ask from your PDF (RAG Q&A)** — Upload a PDF, ask a question in plain
   English, and get an answer grounded in that PDF — with the page number and
   source passage shown, not just a made-up answer. If the answer is not in
   the document, it says so.
2. **Summarise** — A short summary of the chapter / document in simple,
   exam-ready English, plus key points.
3. **Make a quiz** — Multiple-choice questions generated from the PDF, with
   answers shown after you try them.
4. **Generate practice questions** — Exam-style questions from the PDF
   (definition, short answer, and "explain with an example" types), so you
   can practise before an exam.
5. **Flashcards (planned)** — Key term on one side, definition on the other,
   from the same document.

## What it does (v1, already built)
1. Upload a PDF (your notes, a chapter, a paper).
2. The text is split into chunks and indexed for retrieval.
3. Ask a question — the most relevant chunks are retrieved and shown as sources.
4. Answer generation: v1 uses retrieval + an extractive summary from the retrieved
   chunks, so it works with no API key and no cost. An optional LLM step
   (Google Gemini) can be enabled later with your own API key.
5. Quiz mode: generates simple questions from the retrieved chunks.

Tested 2026-11-07 with the Software Engineering answers PDF (12 pages):
retrieval found the correct page for 6/6 in-document questions, and correctly
rejected 2/2 out-of-document questions. Answer extraction needs fixing —
see TEST_RESULTS.md.

## Tech stack
- Python, Streamlit (frontend + deployment)
- PyPDF for PDF text extraction
- scikit-learn TF-IDF for v1 retrieval (no paid API, no heavy model download)
- Planned upgrade: sentence embeddings + FAISS/Chroma, LangChain, Gemini API
- Git, GitHub

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL Streamlit prints, upload a PDF, and ask a question.

## Project structure
```
studylens/
  app.py            # Streamlit UI: upload, ask, sources, summary, quiz, practice questions
  rag.py            # Chunking, TF-IDF retrieval, extractive answer
  requirements.txt
  README.md
  TEST_RESULTS.md   # test log, 2026-11-07
```

## Why this project matters
- It is a *live, demonstrable* project, not just a notebook: a recruiter can
  upload a PDF and test it in under a minute.
- It shows RAG, retrieval, summarisation, question generation, APIs/UI, and
  deployment — the skills missing from Sajeeb's earlier classification-only projects.
- It is useful for higher-study preparation: it is built to study from real notes.

## Roadmap
- [x] v1 skeleton: PDF upload, chunking, TF-IDF retrieval, sources, quiz
- [x] Tested with a real PDF (Software Engineering answers, 2026-11-07)
- [ ] Fix answer extraction: chunk by topic, pick best sentences (not first sentences)
- [ ] Add Summarise mode (short summary + key points)
- [ ] Add real MCQ quiz with answers, and exam-style practice questions
- [ ] Optional Gemini LLM answer step (API key, never committed to GitHub)
- [ ] Deploy free on Streamlit Cloud / Hugging Face Spaces
- [ ] Add the working live link to the resume and GitHub profile

## Safety / honesty notes
- No API keys, passwords, or personal data are committed in this repo.
- Answers are grounded in the uploaded document; if the document does not
  contain the answer, the app says so instead of inventing one.
