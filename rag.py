"""Chunking, TF-IDF retrieval, summarising and question generation for StudyLens v2.

No paid API and no heavy model download. This keeps the demo free, fast,
and runnable on Streamlit Cloud's free tier. The retrieval step is the
honest core of RAG: if the answer is not in the document, say so.

v2 fixes (2026-11-07):
- Chunk by topic/heading, not by whole page, so one chunk = one topic.
- Answer = the sentences closest to the question, not the first sentences
  of the best chunk.
- Summarise: short summary + key points, in document order.
- Real MCQ quiz: definition questions with distractors taken from other
  definitions in the same document (never invented).
- Exam-style practice questions generated from headings / definitions.
"""
import random
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# A line that looks like a numbered heading, e.g. "12. Cyclomatic Complexity"
# or "22. Upper CASE, Lower CASE, and Integrated CASE Tools"
HEADING_RE = re.compile(r"^\s*\d{1,2}\.\s+[A-Z][^\n]{3,80}$", re.MULTILINE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Bullet / artefact characters that appear in extracted PDF text
CLEAN_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text):
    text = CLEAN_RE.sub(" ", text or "")
    text = text.replace("\u00ad", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def split_sentences(text):
    return [s.strip() for s in SENTENCE_RE.split(clean_text(text)) if len(s.strip()) > 20]


def chunk_text(text, chunk_words=150, overlap_words=30):
    """Split text into overlapping word chunks."""
    words = text.split()
    chunks = []
    step = max(1, chunk_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + chunk_words])
        if chunk.strip():
            chunks.append(chunk)
        if start + chunk_words >= len(words):
            break
    return chunks


def split_by_topic(pages):
    """Split pages into topic chunks.

    pages: list of (page_number, page_text).
    Returns chunk dicts: {"page": int, "topic": str, "text": str}.
    A new topic starts at a numbered heading line; text before the first
    heading on a page keeps the previous topic (or "Introduction").
    """
    chunks = []
    topic = "Introduction"
    for page_no, page_text in pages:
        # Split this page's text at heading lines, keeping the heading.
        parts = HEADING_RE.split(page_text)
        headings = HEADING_RE.findall(page_text)
        # parts[0] is text before the first heading; parts[i+1] follows headings[i]
        sections = []
        if parts and clean_text(parts[0]):
            sections.append((topic, parts[0]))
        for heading, body in zip(headings, parts[1:]):
            topic = clean_text(heading)
            if clean_text(body):
                sections.append((topic, body))
        for sec_topic, sec_text in sections:
            for chunk in chunk_text(clean_text(sec_text)):
                chunks.append({"page": page_no, "topic": sec_topic, "text": chunk})
    return chunks


# Backwards-compatible name used by app.py v1
def split_by_pages(pages):
    return split_by_topic(pages)


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in chunks]) if chunks else None

    def retrieve(self, question, top_k=3):
        if not self.chunks or self.matrix is None:
            return []
        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            if scores[i] > 0.05:  # below this, the document probably does not contain it
                results.append({**self.chunks[i], "score": float(scores[i])})
        return results

    def best_sentences(self, question, retrieved, n=3):
        """Pick the n sentences from the retrieved chunks closest to the question."""
        sentences = []
        for r in retrieved:
            for s in split_sentences(r["text"]):
                sentences.append((s, r["page"], r.get("topic", ""), r["score"]))
        if not sentences:
            return []
        try:
            vec = TfidfVectorizer(stop_words="english", max_features=5000)
            mat = vec.fit_transform([s[0] for s in sentences] + [question])
            sims = cosine_similarity(mat[-1], mat[:-1])[0]
        except ValueError:
            return sentences[:n]
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
        picked, seen = [], set()
        for i in ranked:
            s = sentences[i][0]
            if s in seen:
                continue
            seen.add(s)
            picked.append({"text": s, "page": sentences[i][1],
                           "topic": sentences[i][2], "score": float(sims[i])})
            if len(picked) >= n:
                break
        return picked


def extractive_answer(question, retrieved, retriever=None):
    """Answer = best matching sentences, in document order.

    This deliberately does NOT invent an answer. If retrieval is weak,
    the caller should show 'not found in this document'.
    """
    if not retrieved:
        return "I could not find this in the uploaded document. Try rephrasing, or check if that topic is in the PDF."
    if retriever is not None:
        best = retriever.best_sentences(question, retrieved, n=3)
    else:
        best = [{"text": s} for s in split_sentences(retrieved[0]["text"])[:3]]
    if not best:
        return "I could not find this in the uploaded document. Try rephrasing, or check if that topic is in the PDF."
    # Keep document order (page, then original order) for a readable answer.
    return " ".join(b["text"] for b in best)


def summarise(chunks, max_points=8):
    """Extractive summary: first sentence of each topic + key points.

    Returns (summary_text, key_points list of (topic, sentence)).
    Free, no LLM: it quotes the document's own opening sentences.
    """
    topics = []
    seen_topics = set()
    for c in chunks:
        topic = c.get("topic", "Introduction")
        if topic not in seen_topics:
            seen_topics.add(topic)
            topics.append(topic)
    key_points = []
    for c in chunks:
        sents = split_sentences(c["text"])
        if sents and c.get("topic", "") not in [p[0] for p in key_points]:
            key_points.append((c.get("topic", "Introduction"), sents[0]))
        if len(key_points) >= max_points:
            break
    summary = " ".join(s for _, s in key_points[:5])
    if not summary.strip():
        # Fallback for short / table-like PDFs (e.g. a 1-page exam routine):
        # use the raw text of the first chunks, cleaned, instead of saying
        # "could not build a summary". Never invent content.
        raw = " ".join(c["text"] for c in chunks[:3]).strip()
        raw = re.sub(r"\s+", " ", raw)
        if raw:
            summary = raw[:600] + ("..." if len(raw) > 600 else "")
            key_points = [("Document", summary)]
    return summary, key_points


def find_definitions(chunks):
    """Find 'Term is / means / refers to' definition sentences.

    Returns list of (term, definition_sentence, page).
    Term is taken from the chunk topic when possible, otherwise from the
    start of the sentence.
    """
    defs = []
    seen = set()
    for c in chunks:
        for s in split_sentences(c["text"]):
            m = re.match(r"^(.{3,60}?)\s+(is|means|refers to|stands for)\s+(.+)$", s, re.IGNORECASE)
            if m and len(s) > 40:
                term = m.group(1).strip()
                # Skip terms that are just a pronoun / filler
                if term.lower() in ("it", "this", "that", "there", "they"):
                    continue
                key = term.lower()
                if key not in seen:
                    seen.add(key)
                    defs.append((term, s, c["page"]))
    return defs


def make_mcq_quiz(chunks, n=5, seed=42):
    """Real MCQs, built only from definitions found in the document.

    Each question: 'What is <topic>?' with that topic's opening definition
    sentence as the correct option and opening sentences of other topics
    as distractors. Nothing is invented.
    Returns list of {"question", "options", "answer_index", "page"}.
    """
    # One definition per topic: first sentence of its first chunk.
    topic_defs = []
    seen = set()
    for c in chunks:
        topic = re.sub(r"^\d{1,2}\.\s*", "", c.get("topic", "")).strip()
        if not topic or topic in seen or topic == "Introduction":
            continue
        sents = split_sentences(c["text"])
        if sents and len(sents[0]) > 40:
            seen.add(topic)
            topic_defs.append((topic, sents[0], c["page"]))
    if len(topic_defs) < 4:
        return []
    rng = random.Random(seed)
    quiz = []
    for topic, definition, page in topic_defs[:n]:
        others = [d for t, d, _ in topic_defs if t != topic]
        if len(others) < 3:
            continue
        options = [definition] + rng.sample(others, 3)
        rng.shuffle(options)
        quiz.append({
            "question": f"What is {topic}?",
            "options": options,
            "answer_index": options.index(definition),
            "page": page,
        })
    return quiz


def make_practice_questions(chunks, n=8):
    """Exam-style practice questions from headings / topics in the document."""
    topics = []
    for c in chunks:
        t = c.get("topic", "")
        if t and t not in topics and t != "Introduction":
            topics.append(t)
    questions = []
    templates = [
        "Define {t}.",
        "Explain {t} with an example.",
        "What is the difference between {t} and a related concept in this chapter?",
    ]
    for i, t in enumerate(topics[:n]):
        # Strip the leading number, e.g. "12. Cyclomatic Complexity" -> "Cyclomatic Complexity"
        name = re.sub(r"^\d{1,2}\.\s*", "", t).strip()
        questions.append(templates[i % len(templates)].format(t=name))
    return questions


def make_flashcards(chunks, n=8):
    """Flashcards: topic name on the front, its definition on the back.

    Built only from the document: term = topic heading, definition = first
    sentence of that topic. Returns list of {"term", "definition", "page"}.
    """
    cards, seen = [], set()
    for c in chunks:
        topic = re.sub(r"^\d{1,2}\.\s*", "", c.get("topic", "")).strip()
        if not topic or topic in seen or topic == "Introduction":
            continue
        sents = split_sentences(c["text"])
        if sents and len(sents[0]) > 40:
            seen.add(topic)
            cards.append({"term": topic, "definition": sents[0], "page": c["page"]})
        if len(cards) >= n:
            break
    return cards


def make_quiz_questions(retrieved, n=3):
    """Backwards-compatible simple quiz (v1 API). Prefer make_mcq_quiz()."""
    questions = []
    for chunk in retrieved[:n]:
        text = chunk["text"][:220].strip()
        questions.append(f"Based on page {chunk['page']}: what is the main point of this passage?\n\n\"{text}...\"")
    return questions
