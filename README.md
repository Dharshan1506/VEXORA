# VEXORA — Evidence-Grounded University Knowledge Intelligence System

VEXORA is an enterprise multimodal Retrieval-Augmented Generation (RAG) platform tailored for university knowledge management. It unifies academic regulations, exam schedules, hostel policies, and course guidelines into a verified, verifiable knowledge engine that completely rejects hallucinations by anchoring every response in real document chunks, validating evidence before generation, and refusing to answer when sufficient evidence cannot be retrieved.

---

## 1. Project Overview

University documentation is often dispersed across complex, multi-page PDFs, Word documents, slide decks, and scanned policy circulars. Traditional chatbots frequently hallucinate dates, attendance thresholds, exam rules, or grade criteria.

**VEXORA eliminates hallucinated claims** through a multi-stage evidence retrieval and verification architecture:
- Documents are ingested, cleaned, chunked with section and page preservation, and indexed with both dense embeddings and BM25 keywords.
- Questions trigger parallel BM25 keyword search and dense vector search.
- Reciprocal Rank Fusion (RRF) combines sparse and dense candidate rankings into a unified candidate pool.
- A cross-encoder reranker scores each candidate chunk for deep semantic relevance.
- An **Evidence Guard** validates whether the reranked evidence meets strict confidence and relevance criteria before invoking the LLM. If evidence is insufficient, it refuses to answer and prevents hallucination.
- Real citations trace each claim directly to document name, exact page number, and section.

---

## 2. Target Architecture

```
                       USER QUESTION
                             ↓
                    QUERY PREPROCESSING
                             ↓
            ┌─────────────────────────────────┐
            │                                 │
       BM25 SEARCH                      VECTOR SEARCH
   (Keyword / Codes)                 (Semantic / Meaning)
            │                                 │
            ↓                                 ↓
     BM25 CANDIDATES                  VECTOR CANDIDATES
            │                                 │
            └────────────────┬────────────────┘
                             ↓
               RECIPROCAL RANK FUSION (RRF)
                  Score(d) = Σ 1/(k + rank)
                             ↓
                     CANDIDATE SET
                             ↓
                 CROSS-ENCODER RERANKER
             (ms-marco-MiniLM-L-6-v2)
                             ↓
                     EVIDENCE GUARD
           (Score ≥ 0.15 & Relevant Chunks)
                             ↓
             ┌───────────────┴───────────────┐
             │                               │
        SUFFICIENT                      INSUFFICIENT
         EVIDENCE                         EVIDENCE
             │                               │
             ↓                               ↓
         REAL LLM                   DO NOT HALLUCINATE
   (Gemini / OpenAI API)                     │
             │                               ↓
             ↓                         "INSUFFICIENT
       REAL CITATIONS                    EVIDENCE"
     (Doc, Page, Section)                    │
             │                               ↓
             └───────────────┬───────────────┘
                             ↓
                        FINAL ANSWER
```

---

## 3. Tech Stack

- **Frontend**: React 18, Vite, Vanilla CSS + Tailwind CSS, Lucide React, Three.js (3D Knowledge Core Particle Field), Recharts.
- **Backend**: FastAPI, Uvicorn, Pydantic v2, Python-Multipart.
- **Database**: SQLite with WAL mode (`vexora_knowledge.db`), relational schema with performance indexes.
- **Authentication**: PBKDF2-HMAC-SHA256 password hashing + PyJWT bearer authentication.
- **Document Extraction**:
  - PDF: PyMuPDF (`pymupdf`) with page-by-page text extraction and fallback OCR for scanned pages.
  - DOCX: `python-docx` with paragraph-to-virtual-page segmentation.
  - PPTX: `python-pptx` with slide-to-page mapping.
  - Plain Text: Python native reader with line-based page slicing.
  - Images: `Pillow` + `pytesseract` OCR with word-confidence tracking.
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dimensional normalized vectors), optional Google GenAI `text-embedding-004`.
- **Keyword Retrieval**: `rank-bm25` (Okapi BM25 implementation).
- **Reranker**: `sentence-transformers` CrossEncoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
- **LLM Synthesis**: Google GenAI SDK (`gemini-2.0-flash`) or OpenAI-compatible endpoints.

---

## 4. Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13)
- Node.js 18+ and npm
- (Optional for scanned image files) Tesseract OCR

### Step 1: Clone and Set Up Backend
```bash
cd backend
py -m pip install -r requirements.txt
```

### Step 2: Set Up Frontend
```bash
# In the project root directory
npm install
```

---

## 5. Environment Variables

Copy `backend/.env.example` to `backend/.env`:
```bash
cp backend/.env.example backend/.env
```

Configuration reference:
```ini
# ── Authentication ─────────────────────────────────────────────────────────────
JWT_SECRET_KEY=your-secure-random-jwt-secret-string-here

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///vexora_knowledge.db

# ── LLM Configuration ─────────────────────────────────────────────────────────
LLM_PROVIDER=gemini                     # 'gemini' or 'openai'
GEMINI_API_KEY=your-gemini-api-key-here # Get from https://aistudio.google.com/app/apikey
LLM_MODEL=gemini-2.0-flash

# Alternative for OpenAI-compatible endpoints (Ollama, Groq, OpenRouter):
# LLM_API_KEY=your-api-key
# LLM_BASE_URL=https://api.openai.com/v1

# ── Embedding Configuration ────────────────────────────────────────────────────
EMBEDDING_PROVIDER=sentence-transformers # 'sentence-transformers' or 'gemini'
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ── Chunking Configuration ────────────────────────────────────────────────────
CHUNK_SIZE=500
CHUNK_OVERLAP=100
MIN_CHUNK_WORDS=30

# ── Retrieval & Reranker ───────────────────────────────────────────────────────
BM25_TOP_K=10
VECTOR_TOP_K=10
RRF_K=60
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=5

# ── Evidence Guard ─────────────────────────────────────────────────────────────
EVIDENCE_SCORE_THRESHOLD=0.15
EVIDENCE_MIN_CHUNKS=1

# ── Debug Mode ────────────────────────────────────────────────────────────────
DEBUG_RETRIEVAL=false
```

---

## 6. Database Setup

The database initializes automatically on backend startup via the FastAPI `lifespan` handler. You can also manually initialize it:
```bash
py backend/database.py
```

Default seeded accounts:
- **Admin**: `admin@vexora.edu` / `Admin@2026`
- **Student**: `student@vexora.edu` / `Student@2026`
- **Scholar**: `scholar@university.edu` / `Scholar@2026`

---

## 7. How to Run Backend

From the project root or backend directory:
```bash
py backend/main.py
```
The FastAPI server starts on `http://127.0.0.1:8000`.
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

---

## 8. How to Run Frontend

In a separate terminal:
```bash
npm run dev
```
The Vite development server runs on `http://localhost:8080`.
Log in using one of the default accounts or register a new account.

To create a production build:
```bash
npm run build
```

---

## 9. How Document Ingestion Works

1. **Upload**: User uploads PDF, DOCX, PPTX, TXT, PNG, JPG, or WEBP via `POST /api/documents/upload`.
2. **Validation**: Extension validation and maximum size check (50 MB).
3. **Hashing**: SHA-256 hash computed for document deduplication and version tracking.
4. **Text Extraction**:
   - PyMuPDF extracts text page by page.
   - If selectable text is below 30 characters, OCR is automatically triggered.
   - DOCX paragraphs and PPTX slides are mapped to virtual pages.
5. **Text Cleaning**:
   - `clean_document_text` removes null bytes and control characters.
   - Normalizes consecutive spaces, line endings, and excessive blank lines.
6. **Chunking**:
   - Sliding-window word chunker (`CHUNK_SIZE=500`, `CHUNK_OVERLAP=100`).
   - Section heading detection preserves context.
7. **Embeddings**:
   - Batch encoding computes 384-dimensional dense vectors using `SentenceTransformer`.
8. **Storage & Indexing**:
   - Document metadata stored in `documents`.
   - Chunk text, section, page, OCR confidence, and embeddings stored in `document_chunks`.
   - Version history saved in `document_versions`.
   - Document status transitions to `indexed`.

---

## 10. How BM25 Works

- Implemented via `rank_bm25.BM25Okapi` in [retrieval_service.py](file:///d:/AI_CHATBOT/backend/services/retrieval_service.py).
- Operates over actual indexed document chunks loaded from SQLite.
- Custom tokenizer preserves alphanumeric terms, percentages (e.g. `80%`), decimal numbers, and abbreviations.
- Calculates exact term-frequency / inverse-document-frequency relevance scores.
- Ranks chunks by BM25 score descending and returns top-K candidates.

---

## 11. How Vector Search Works

- Implemented using numpy dense cosine similarity in [retrieval_service.py](file:///d:/AI_CHATBOT/backend/services/retrieval_service.py).
- The user query is embedded into the same 384-dimensional vector space using `embed_text(query)`.
- Cosine similarity: `dot(u, v) / (norm(u) * norm(v))`.
- Overcomes vocabulary mismatch and handles natural-language paraphrases (e.g., "sit for exams" matching "eligible to appear for semester end examinations").

---

## 12. How RRF (Reciprocal Rank Fusion) Works

RRF combines the ranked outputs of BM25 and vector search without needing score calibration:
$$\text{RRF Score}(d) = \sum_{m \in \{\text{BM25}, \text{Vector}\}} \frac{1}{k + \text{rank}_m(d)}$$
Where $k = 60$ by default.
- Implemented in `rrf_fusion()` in [retrieval_service.py](file:///d:/AI_CHATBOT/backend/services/retrieval_service.py).
- Chunks appearing high in both keyword and semantic searches are prioritized.
- Each chunk preserves `rrf_score`, `bm25_rank`, `vector_rank`, `bm25_score`, and `vector_score`.

---

## 13. How Cross-Encoder Reranking Works

- Implemented in [reranker_service.py](file:///d:/AI_CHATBOT/backend/services/reranker_service.py).
- Uses `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Unlike bi-encoders, the cross-encoder performs full cross-attention over `(query, chunk_content)` pairs simultaneously.
- Produces an absolute relevance score.
- Returns the top 3–5 highest-scoring evidence chunks.

---

## 14. Evidence Guard

Located in [llm_service.py](file:///d:/AI_CHATBOT/backend/services/llm_service.py), the **Evidence Guard** is a critical safety component:
- Checks:
  1. Were any chunks retrieved?
  2. Does the count meet `EVIDENCE_MIN_CHUNKS`?
  3. Is the top cross-encoder score $\ge \text{EVIDENCE\_SCORE\_THRESHOLD}$ (default `0.15`)?
- **Behavior**:
  - If **sufficient**: Passes retrieved evidence to the LLM for grounded synthesis.
  - If **insufficient**: Completely blocks LLM generation and returns:
    `"I couldn't find sufficient evidence in the available university documents to answer this reliably."`
  - Zero hallucination is guaranteed by refusing to fabricate ungrounded answers.

---

## 15. Citation System

- Citations are built dynamically from real document chunk metadata.
- Preserves:
  - Document Name
  - Real Page Number (or null if unpaged, never fabricated)
  - Section Name
  - Relevance Score
- In the frontend, citations appear as clickable badges (`[1] Academic Regulations 2026.pdf (p.2)`).
- Clicking a citation highlights the exact excerpt in the Grounding Evidence panel and opens the document viewer.

---

## 16. Version Management

- When a newer document is uploaded:
  - System checks base filename and content hash.
  - Identifies existing superseded document records.
  - Sets `superseded_by` pointer on older document.
  - Stores entry in `document_versions`.
- **Retrieval Awareness**:
  - `load_all_chunks(prefer_latest=True)` excludes superseded versions from primary retrieval so latest rules take precedence.
  - Historical versions remain preserved in `document_versions` for inspection in the Vault.

---

## 17. Conflict Detection

- At document upload and at query time, the system compares numerical policies (e.g. attendance percentage thresholds) across retrieved sources.
- If conflicting percentages are found (e.g. 75% in an older policy vs 85% in an updated regulation), VEXORA detects the discrepancy and explicitly reports:
  `⚠️ Conflicting Information Detected: Document A cites 75% vs Document B cites 85%.`
- Conflicts are stored in `document_conflicts` and can be explored in the Document Conflict Detector view.

---

## 18. Testing

The project includes an end-to-end test suite in [tests/test_rag_pipeline.py](file:///d:/AI_CHATBOT/tests/test_rag_pipeline.py) covering all 7 pipeline criteria:

```bash
py -m pytest tests/test_rag_pipeline.py -v -s
```

Tested scenarios:
1. `test_test1_upload_real_pdf`: Real PDF creation, text extraction, sliding-window chunking, dense embedding, DB indexing.
2. `test_test2_question_with_known_answer`: BM25 + Vector + RRF + Cross-Encoder + Evidence Guard + Grounded answer + Citation tracking.
3. `test_test3_question_without_evidence_no_hallucination`: Verification that unrelated questions are blocked by the Evidence Guard with the exact refusal message.
4. `test_test4_semantic_retrieval_paraphrase`: Semantic vector retrieval of paraphrased questions.
5. `test_test5_conflicting_documents_detection`: Detection of conflicting numeric values between documents.
6. `test_test6_document_version_management`: Prioritizing latest version and excluding superseded documents.
7. `test_test7_conversation_persistence`: Saving and reloading conversation history with citations and evidence status from SQLite.

---

## 19. Troubleshooting

- **`Tesseract OCR not found`**: OCR is optional for selectable PDFs and text documents. To enable OCR for images or scanned PDFs, install Tesseract OCR from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system PATH or set `TESSERACT_CMD` in `.env`.
- **`First embedding run is slow`**: On first run, `sentence-transformers` downloads the ~80 MB `all-MiniLM-L6-v2` model weights to your local Hugging Face cache. Subsequent runs load instantly from disk.
- **`Gemini API Key missing`**: If `GEMINI_API_KEY` is not provided, VEXORA still runs BM25 + Vector + RRF + Cross-Encoder + Evidence Guard and displays the verified retrieved evidence directly, without failing.
