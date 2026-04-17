# BookInsight (Book Intelligence Platform)

Full-stack AI/RAG web application: scrape and catalog books, browse them in a React dashboard, and chat with **BookInsight**—a RAG assistant that combines your **local vector store (Chroma + sentence-transformers)** with **Google Books** and **Open Library** snippets, answered by a **local LLM** via **LM Studio** (OpenAI-compatible API on port `1234`).

**Submission checklist**

- Push this repository to **GitHub** and paste the repo URL in the course form: [Submission form](https://forms.gle/Fby8pMSmBJqjuVf56).
- Add **3–4 UI screenshots** under `assets/screenshots/` (see filenames below) and commit them.

---

## UI screenshots

Place your images in [`assets/screenshots/`](assets/screenshots/) using these names so the links below work on GitHub:

| # | File | Suggested content |
|---|------|-------------------|
| 1 | `01-dashboard.png` | Book listing / dashboard |
| 2 | `02-book-detail.png` | Single book detail view |
| 3 | `03-qa-chat.png` | RAG / BookInsight Q&A chat |
| 4 | `04-optional-loading-or-error.png` | Loading state, empty state, or error banner (optional) |

![Dashboard](assets/screenshots/01-dashboard.png)

![Book detail](assets/screenshots/02-book-detail.png)

![Q&A chat — BookInsight](assets/screenshots/03-qa-chat.png)

![Optional — loading or error state](assets/screenshots/04-optional-loading-or-error.png)

> **Note:** Until you add the real PNG files, those links may show as broken on GitHub—that is expected until you attach your screenshots.

---

## Tech stack

| Layer | Technology |
|--------|------------|
| Backend | Django + Django REST Framework |
| DB | SQLite (metadata) |
| Vector store | ChromaDB + `sentence-transformers` embeddings |
| Frontend | React 19 + Vite + Tailwind CSS |
| Automation | Selenium (scraping flows) |
| LLM | LM Studio at `http://127.0.0.1:1234` (local inference) |

---

## Setup instructions

### Prerequisites

- **Python** 3.10+ (3.11+ recommended)
- **Node.js** 20+ and npm
- **LM Studio** (or any OpenAI-compatible server on `127.0.0.1:1234`) with a chat model loaded and the local server started

### 1) Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd config
python manage.py migrate
python manage.py runserver
```

API base URL: **`http://127.0.0.1:8000/api`**

### 2) Frontend

```powershell
cd frontend-react
npm install
npm run dev
```

App URL: **`http://localhost:5173`**

Optional: create `frontend-react/.env` from `.env.example` if you need a custom API base:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 3) LM Studio (required for `/ask/` and `/analyze/`)

1. Open LM Studio, download a **chat** model (e.g. Llama 3 instruct family).
2. Start the **Local Server** on **`http://127.0.0.1:1234`**.
3. Enable **OpenAI-compatible** chat completions.

### 4) Run automated smoke tests (optional)

From `backend/config` with venv activated:

```powershell
..\venv\Scripts\python.exe manage.py test books
```

### 5) Manual API samples

See [`samples/api.http`](samples/api.http) and the JSON bodies in [`samples/`](samples/) for copy-paste testing with REST Client or similar tools.

---

## API documentation

Base URL: **`http://127.0.0.1:8000/api`**

All JSON responses use DRF `Response` shapes; errors return `status: "error"` or HTTP 4xx/5xx with a `message` / `error` field where applicable.

### Books

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/books/` | List all books (`status`, `data[]`). |
| `GET` | `/books/<id>/` | Book detail by primary key. |
| `POST` | `/add-book/` | Create a book. Body: `title`, `author`, optional `description`, `rating`, `url`. |
| `GET` | `/scrape-books/` | Trigger scraping pipeline (Selenium; environment-dependent). |
| `GET` | `/books/<id>/related/` | Related picks using local + web heuristics. |
| `GET` | `/summary/<id>/` | Short text summary from stored description. |

### RAG Q&A (BookInsight)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ask/` | Main chat: RAG + Google Books + Open Library + LM Studio. |
| `GET` | `/chat-history/` | Recent stored Q&A rows from the database. |

**`POST /ask/` body**

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| `question` | string | Yes | Latest user message. |
| `conversation` | array | No | Prior turns: `{ "role": "user" \| "assistant", "content": "..." }[]`. |

**`POST /ask/` success response (shape)**

```json
{
  "status": "success",
  "question": "…",
  "answer": "…",
  "citations": ["…"],
  "cached": false
}
```

### Insights & recommendations

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/recommend/` | Body: `{ "query": "science fiction underwater" }`. |
| `POST` | `/sentiment/` | Rule-based sentiment on `text`. |
| `POST` | `/genre/` | Rule-based genre guess on `text`. |
| `POST` | `/analyze/` | Sentiment + genre via LM Studio (same host as Q&A). |

---

## Optional environment variables (backend)

| Variable | Purpose |
|----------|---------|
| `LM_STUDIO_URL` | Base URL for LM Studio (default `http://127.0.0.1:1234`). |
| `LM_STUDIO_READ_TIMEOUT` | Read timeout seconds for LLM HTTP calls. |
| `LM_STUDIO_MAX_CONTEXT_CHARS` | Max retrieved context characters sent to the LLM. |
| `LM_STUDIO_MAX_TOKENS` / `LM_STUDIO_TEMPERATURE` | Generation caps / sampling. |
| `WEB_FETCH_WALL_SEC` | Max wall time for parallel Google Books + Open Library fetches. |
| `GOOGLE_BOOKS_MAX_RESULTS` | Volume count for Google Books. |
| `OPEN_LIBRARY_LIMIT` | Rows from Open Library search. |

---

## Sample questions and answers

These illustrate how the system is **intended** to behave once LM Studio is running and optional web catalogs respond. Exact wording varies by model and retrieval.

**Q1:** “What is the *Ramayana* about?”  

**A1 (expected style):** A concise plot/theme overview grounded in retrieved snippets (your DB + Open Library / Google Books when available), with optional follow-up like whether they want children’s retellings or scholarly translations.

**Q2:** “Recommend literary fiction under 300 pages.”  

**A2:** A short bullet list of plausible titles, mixing catalog hits with well-known slim novels, plus one clarifying question (e.g. preferred tone: bleak vs. comic).

**Q3 (multi-turn):**  

- User: “I liked *Sapiens*—what’s next?”  
- Assistant: suggests similar big-history / idea books.  
- User: “Something shorter and more narrative?”  

**A3:** Narrows to mid-length narrative nonfiction, still citing or aligning with any retrieved context.

**Example `POST /ask/` payload** (single-turn) — also in [`samples/post_ask.json`](samples/post_ask.json):

```json
{
  "question": "Recommend three literary novels under 300 pages.",
  "conversation": []
}
```

---

## Project structure (high level)

```
aibookinsight/
├── backend/
│   ├── requirements.txt
│   └── config/              # Django project root (manage.py)
│       ├── books/           # Models, views, RAG, URLs
│       └── config/          # settings, root URLconf
├── frontend-react/          # Vite + React UI
├── samples/                 # Example HTTP + JSON for manual tests
└── assets/screenshots/      # Your 3–4 UI screenshots (PNG)
```

---

## License / course use

Use and modify for coursework submission as required by your institution.
