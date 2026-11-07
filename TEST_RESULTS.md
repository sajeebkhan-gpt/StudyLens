# StudyLens — Test results

## v2 test, 2026-11-07 (after fix)
Tested with: `~/workspace/your_files/software-engineering-answers.pdf`
(12 pages, 4,474 words, 49 topic chunks)

### Answer extraction — FIXED, 8/8
- 6/6 in-document questions now answer with the correct topic sentences:
  - Cyclomatic complexity → "Cyclomatic complexity is a measure of how complex a program's control flow is. … V(G) = E - N + 2P …"
  - Verification vs validation → "Verification and validation (V&V) are the two sides of checking software quality. Verification can be done without running the code …"
  - Cohesion and coupling → correct, high cohesion / low coupling
  - Availability and reliability → correct, different measures
  - CASE tools → correct, "CASE tools are software tools that support the software development process …"
  - Encapsulation / inheritance / polymorphism → correct
- 2/2 out-of-document questions correctly rejected:
  - "capital of France" → "I could not find this in the uploaded document."
  - "how to cook biryani" → same
- Fix: chunk by topic/heading (~150 words) instead of whole pages, and pick
  the sentences closest to the question (TF-IDF cosine) instead of the
  first 3 sentences of the chunk.

### Summarise — WORKS
- Summary built from first sentence of each topic, in document order.
- Key points: 8 topics listed with their opening sentence.
- Example first point: "A structural model shows the static structure of a system: what the parts are, and how they are connected."

### MCQ quiz — FIXED, 5/5 usable
- v2 uses one definition per topic (first sentence of the topic) as the
  correct option, with other topics' definitions as distractors.
- Example: "What is Structural Models?" → correct: "A structural model shows the static structure of a system …"
- v1 MCQ was bad (garbage terms like "Each topic?") — replaced, do not use v1 logic.

### Practice questions — WORKS
- 8 exam-style questions generated from headings, e.g.:
  - "Define Structural Models."
  - "Explain Design and Implementation, Object-Oriented Design (OOD) with an example."
  - "What is the difference between Architectural Design, Views and Decisions and a related concept in this chapter?"

### Flashcards — WORKS (v2 final)
- Term on the front (topic name), definition on the back (first sentence
  of that topic), with a Show/Hide button. Built only from the document.

### Streamlit app — LOADS
- `streamlit run app.py` returns HTTP 200 locally, 5 tabs: Ask / Summarise / Quiz / Practice Questions / Flashcards.

## v1 test, 2026-11-07 (before fix, for comparison)
- Retrieval 6/6 correct pages, out-of-doc 2/2 correctly rejected.
- Answer quality FAILED: answers started on the wrong topic because chunks
  were whole pages and the answer was the first 3 sentences of the chunk.
- Quiz was generic ("what is the main point?").

## Next steps
1. Sajeeb reviews v2 features.
2. Deploy to Streamlit Cloud — free tier. Needs: GitHub repo with this code
   (Sajeeb pushes it, or signs in via browser), then Streamlit Cloud deploy.
3. Re-test live link with the same 8 questions after deployment.
