"""
REST API for BookInsight: book catalog, scraping, RAG Q&A, and web-augmented chat.

Q&A flow (``ask_question``): local Chroma retrieval → parallel Google Books + Open
Library snippets → LM Studio (OpenAI-compatible) completion with optional
multi-turn ``conversation`` from the client.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .models import Book, ChatHistory
from .rag import add_to_vector_db, query_vector_db

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, wait


def _lm_studio_chat_url() -> str:
    base = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:1234").rstrip("/")
    return f"{base}/v1/chat/completions"


def _lm_studio_timeout():
    """(connect, read) — local LLMs often need a long read timeout on CPU."""
    connect = float(os.environ.get("LM_STUDIO_CONNECT_TIMEOUT", "15"))
    read = float(os.environ.get("LM_STUDIO_READ_TIMEOUT", "240"))
    return (connect, read)


# Cap RAG context sent to the local LLM (smaller = faster local inference).
_LM_MAX_CONTEXT_CHARS = int(os.environ.get("LM_STUDIO_MAX_CONTEXT_CHARS", "6000"))

_BOOK_INSIGHT_SYSTEM = """You are BookInsight: a concise, friendly book guide.

Use: (1) retrieved DB chunks, (2) Google Books / Open Library snippets in this message, (3) general literary knowledge when needed—note when you are not citing snippets.

Be brief by default (roughly 2–5 short paragraphs unless the user asks for depth). Bullets for book lists. One follow-up question at the end when natural. Do not invent dates, awards, or ISBNs."""

_HTTP_HEADERS_OL = {"User-Agent": "BookInsight/1.0 (local educational project)"}


def _normalize_conversation(raw):
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not str(content).strip():
            continue
        max_turn_chars = int(os.environ.get("CHAT_TURN_MAX_CHARS", "2500"))
        out.append({"role": role, "content": str(content).strip()[:max_turn_chars]})
    return out[-12:]


def _fetch_google_books(question: str) -> tuple[str, list]:
    """Returns (snippet_block, titles) for merging into RAG context."""
    q = (question or "").strip()
    if len(q) < 2:
        return "", []
    max_results = int(os.environ.get("GOOGLE_BOOKS_MAX_RESULTS", "5"))
    req_timeout = float(os.environ.get("GOOGLE_BOOKS_TIMEOUT", "4"))
    queries = [q]
    if os.environ.get("BOOKINSIGHT_EXTRA_GOOGLE_QUERY", "0") == "1":
        queries.append(f"{q} books")
    seen = set()
    block = ""
    titles_out = []
    for query in queries:
        try:
            gv_response = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": query, "maxResults": max(2, max_results // len(queries))},
                timeout=req_timeout,
            )
            if gv_response.status_code != 200:
                continue
            for item in gv_response.json().get("items") or []:
                volume_info = item.get("volumeInfo", {})
                title = volume_info.get("title") or "Unknown Title"
                key = str(title).lower()
                if key in seen:
                    continue
                seen.add(key)
                authors = ", ".join(volume_info.get("authors", ["Unknown Author"]))
                desc = volume_info.get("description", "") or "No description."
                if len(desc) > 220:
                    desc = desc[:220] + "..."
                block += f"Title: {title}\nAuthor(s): {authors}\nDescription: {desc}\n\n"
                titles_out.append(title)
        except Exception:
            continue
    return block, titles_out


def _fetch_open_library(question: str) -> tuple[str, list]:
    q = (question or "").strip()
    if len(q) < 2:
        return "", []
    limit = int(os.environ.get("OPEN_LIBRARY_LIMIT", "4"))
    req_timeout = float(os.environ.get("OPEN_LIBRARY_TIMEOUT", "5"))
    try:
        ol_response = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": q, "limit": limit},
            timeout=req_timeout,
            headers=_HTTP_HEADERS_OL,
        )
        if ol_response.status_code != 200:
            return "", []
        docs = ol_response.json().get("docs") or []
    except Exception:
        return "", []

    seen = set()
    block = ""
    titles_out = []
    for doc in docs[:limit]:
        title = doc.get("title")
        if isinstance(title, list):
            title = title[0] if title else "Unknown Title"
        if not title:
            title = "Unknown Title"
        key = str(title).lower()
        if key in seen:
            continue
        seen.add(key)

        authors = doc.get("author_name") or []
        if isinstance(authors, list):
            authors_str = ", ".join(authors[:3]) if authors else "Unknown Author"
        else:
            authors_str = str(authors)

        first = doc.get("first_sentence")
        if isinstance(first, list) and first:
            first = first[0]
        elif not isinstance(first, str):
            first = ""
        if first and len(first) > 160:
            first = first[:160] + "..."

        subjects = doc.get("subject") or []
        if isinstance(subjects, list):
            subj = ", ".join(str(s) for s in subjects[:3])
        else:
            subj = str(subjects) if subjects else ""

        line = f"Title: {title}\nAuthor(s): {authors_str}\n"
        if first:
            line += f"First line: {first}\n"
        if subj:
            line += f"Subjects: {subj}\n"
        line += "\n"
        block += line
        titles_out.append(str(title))

    return block, titles_out


def _merge_web_results(context: str, cited_sources: list, g_block: str, g_titles: list, o_block: str, o_titles: list) -> str:
    for t in g_titles:
        if t not in cited_sources:
            cited_sources.append(t)
    for t in o_titles:
        if t not in cited_sources:
            cited_sources.append(t)
    if g_block:
        context += "\n--- Web Context (Google Books) ---\n" + g_block
    if o_block:
        context += "\n--- Web Context (Open Library) ---\n" + o_block
    return context


# =========================
# GET BOOKS API
# =========================
@api_view(['GET'])
def get_books(request):
    try:
        books = Book.objects.all().values()
        return Response({
            "status": "success",
            "data": list(books)
        })
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

@api_view(['GET'])
def get_book_detail(request, book_id):
    try:
        book = get_object_or_404(Book, id=book_id)
        return Response({
            "status": "success",
            "data": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "rating": book.rating,
                "url": book.url,
            }
        })
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)


# =========================
# ADD BOOK API
# =========================
@api_view(['POST'])
def add_book(request):
    try:
        data = request.data

        if not data.get('title') or not data.get('author'):
            return Response({"error": "Missing required fields"}, status=400)

        book = Book.objects.create(
            title=data.get('title'),
            author=data.get('author'),
            description=data.get('description', ''),
            rating=data.get('rating'),
            url=data.get('url', '')
        )

        try:
            add_to_vector_db(book.id, book.title, book.description)
        except Exception as e:
            print("Vector DB error:", e)

        return Response({
            "status": "success",
            "message": "Book added",
            "id": book.id
        })

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)


# =========================
# SCRAPING API
# =========================
@api_view(['GET'])
def scrape_books(request):
    driver = None

    try:
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--headless=new")

        # Selenium Manager will auto-resolve driver when possible.
        driver = webdriver.Chrome(options=options)

        url = "https://books.toscrape.com/"
        driver.get(url)

        wait = WebDriverWait(driver, 10)

        elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3 a"))
        )

        saved_books = []

        for el in elements[:10]:
            title = el.get_attribute("title")

            book = Book.objects.create(
                title=title,
                author="Unknown",
                description="Scraped data from website",
                rating=4.0,
                url=url
            )

            try:
                add_to_vector_db(book.id, book.title, book.description)
            except Exception as e:
                print("Vector DB error:", e)

            saved_books.append({
                "id": book.id,
                "title": title
            })

        return Response({
            "status": "success",
            "count": len(saved_books),
            "message": "Books scraped and stored successfully",
            "data": saved_books
        })

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)

    finally:
        if driver:
            driver.quit()





# =========================
# AI SUMMARY
# =========================
@api_view(['GET'])
def book_summary(request, book_id):
    try:
        book = Book.objects.get(id=book_id)

        text = book.description or book.title
        summary = text[:150] + "..." if len(text) > 150 else text

        return Response({
            "status": "success",
            "title": book.title,
            "summary": summary
        })

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)


# =========================
# Q&A API (RAG + web catalogs + LM Studio)
# =========================

@api_view(['POST'])
def ask_question(request):
    try:
        question = request.data.get('question', '')

        if not question:
            return Response({
                "status": "error",
                "message": "Please provide a question"
            }, status=400)

        conversation = _normalize_conversation(request.data.get("conversation"))
        if conversation:
            cache_basis = json.dumps(conversation, ensure_ascii=False) + "\n" + question.strip().lower()
            cache_key = f"ask:conv:{hashlib.md5(cache_basis.encode('utf-8')).hexdigest()}"
        else:
            cache_key = f"ask:{hashlib.md5(question.strip().lower().encode('utf-8')).hexdigest()}"

        cached_payload = cache.get(cache_key)
        
        # Invalidate cache if it contains an error message.
        if cached_payload:
            ans = str(cached_payload.get("answer", ""))
            if "Error:" in ans or "LLM server" in ans:
                cache.delete(cache_key)
                cached_payload = None
                
        if cached_payload:
            return Response({
                **cached_payload,
                "cached": True,
            })

        # Create context
        context = "--- Local Vector Database Context (ChromaDB API) ---\n"
        cited_sources = []
        
        # 1. Get contextual books based on semantic embedding similarity from VectorDB
        semantic_chunks = query_vector_db(question, n_results=4)
        if semantic_chunks:
            for chunk in semantic_chunks:
                context += f"{chunk}\n\n"
                first_line = chunk.split("\n")[0].replace("Title:", "").strip()
                if first_line and first_line not in cited_sources:
                    cited_sources.append(first_line)
        else:
            # Fallback to general DB if vector DB is empty
            books = Book.objects.all()[:3]
            for book in books:
                context += f"Title: {book.title}\nDescription: {book.description}\n\n"
                if book.title not in cited_sources:
                    cited_sources.append(book.title)

        # 2–3. Web catalogs in parallel (wall-clock cap so the UI does not wait forever)
        wall = float(os.environ.get("WEB_FETCH_WALL_SEC", "6"))
        g_block, g_titles = "", []
        o_block, o_titles = "", []
        try:
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_g = ex.submit(_fetch_google_books, question)
                f_o = ex.submit(_fetch_open_library, question)
                wait([f_g, f_o], timeout=wall)
            for fut in (f_g, f_o):
                if not fut.done():
                    continue
                try:
                    blk, titles = fut.result(timeout=0)
                except Exception:
                    blk, titles = "", []
                if fut is f_g:
                    g_block, g_titles = blk, titles
                else:
                    o_block, o_titles = blk, titles
        except Exception:
            pass
        context = _merge_web_results(context, cited_sources, g_block, g_titles, o_block, o_titles)

        context_for_llm = context
        if len(context_for_llm) > _LM_MAX_CONTEXT_CHARS:
            context_for_llm = (
                context_for_llm[:_LM_MAX_CONTEXT_CHARS]
                + "\n\n[Context truncated for faster local inference.]"
            )

        final_user_content = (
            f"--- Retrieved context ---\n{context_for_llm}\n--- End context ---\n\n"
            f"User:\n{question.strip()}"
        )

        lm_messages = [{"role": "system", "content": _BOOK_INSIGHT_SYSTEM}]
        for turn in conversation:
            lm_messages.append({"role": turn["role"], "content": turn["content"]})
        lm_messages.append({"role": "user", "content": final_user_content})

        try:
            temp = float(os.environ.get("LM_STUDIO_TEMPERATURE", "0.72"))
        except ValueError:
            temp = 0.72
        try:
            max_tok = int(os.environ.get("LM_STUDIO_MAX_TOKENS", "650"))
        except ValueError:
            max_tok = 650

        # Call LM Studio local LLM (OpenAI compatible endpoint)
        try:
            payload = {
                "messages": lm_messages,
                "temperature": temp,
                "max_tokens": max_tok,
            }
            lm_response = requests.post(
                _lm_studio_chat_url(),
                json=payload,
                timeout=_lm_studio_timeout(),
            )
            lm_response.raise_for_status()
            answer = lm_response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # Fallback answer keeps endpoint responsive
            answer = (
                f"LLM server is currently unavailable ({str(e)}). Here is retrieved context:\n\n"
                + context[:1500]
            )

        payload = {
            "status": "success",
            "question": question,
            "answer": answer,
            "citations": cited_sources[:8],
            "cached": False,
        }
        
        # Do not cache or save any type of setup error or fallback error
        is_error_answer = "LLM server is currently unavailable" in answer
        
        if not is_error_answer:
            cache.set(cache_key, payload, timeout=60 * 60)
            ChatHistory.objects.create(
                question=question,
                answer=answer,
                citations=payload["citations"],
            )
            
        return Response(payload)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['POST'])
def sentiment_analysis(request):
    try:
        text = request.data.get("text", "")

        if not text:
            return Response({"error": "Text is required"}, status=400)

        # Simple rule-based sentiment (no external API needed)
        positive_words = ["good", "great", "excellent", "amazing", "love", "wonderful", "best"]
        negative_words = ["bad", "worst", "boring", "poor", "hate", "terrible", "waste"]

        text_lower = text.lower()

        pos_score = sum(word in text_lower for word in positive_words)
        neg_score = sum(word in text_lower for word in negative_words)

        if pos_score > neg_score:
            sentiment = "Positive 😊"
        elif neg_score > pos_score:
            sentiment = "Negative 😞"
        else:
            sentiment = "Neutral 😐"

        return Response({
            "status": "success",
            "text": text,
            "sentiment": sentiment,
            "positive_score": pos_score,
            "negative_score": neg_score
        })

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['POST'])
def classify_genre(request):
    try:
        text = request.data.get("text", "")

        if not text:
            return Response({"error": "Text is required"}, status=400)

        text_lower = text.lower()

        # Simple keyword-based classification
        if any(word in text_lower for word in ["history", "war", "ancient", "civilization"]):
            genre = "History"
        elif any(word in text_lower for word in ["love", "romance", "relationship"]):
            genre = "Romance"
        elif any(word in text_lower for word in ["magic", "dragon", "fantasy", "kingdom"]):
            genre = "Fantasy"
        elif any(word in text_lower for word in ["science", "technology", "physics", "ai"]):
            genre = "Science"
        elif any(word in text_lower for word in ["god", "epic", "myth", "ramayana", "mahabharata"]):
            genre = "Mythology"
        else:
            genre = "General"

        return Response({
            "status": "success",
            "text": text,
            "genre": genre
        })

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['POST'])
def analyze_text(request):
    try:
        text = request.data.get("text", "")

        if not text:
            return Response({"error": "Text is required"}, status=400)

        prompt = f"""
Analyze the following text from a user asking about books.
Determine the Sentiment (e.g., Positive 😊, Negative 😞, Neutral 😐) and the Genre (e.g., History, Romance, Fantasy, Science, Fiction, General).
Respond ONLY with a valid JSON object in this exactly format:
{{"sentiment": "<sentiment>", "genre": "<genre>"}}

Text: "{text}"
"""
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
            lm_response = requests.post(
                _lm_studio_chat_url(),
                json=payload,
                timeout=_lm_studio_timeout(),
            )
            lm_response.raise_for_status()
            content = lm_response.json()["choices"][0]["message"]["content"].strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            parsed = json.loads(content.strip())
            sentiment = parsed.get("sentiment", "Neutral 😐")
            genre = parsed.get("genre", "General")
        except Exception:
            sentiment = "Neutral 😐"
            genre = "General"

        return Response({
            "status": "success",
            "text": text,
            "sentiment": sentiment,
            "genre": genre
        })

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
def _build_recommendations(query: str):
    if not query:
        return []

    recommendations = []

    # 1. Search local database
    books = Book.objects.all()
    for book in books:
        score = 0
        text = ((book.title or "") + " " + (book.description or "")).lower()

        if query in text:
            score += 2
        for word in query.split():
            if word in text:
                score += 1

        if score > 0:
            recommendations.append({
                "title": book.title,
                "author": book.author,
                "score": score,
                "source": "Local"
            })

    # 2. Search Web (Google Books API)
    try:
        response = requests.get(
            f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=5",
            timeout=8
        )
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            for item in items:
                volume_info = item.get("volumeInfo", {})
                title = volume_info.get("title", "Unknown Title")
                authors = volume_info.get("authors", ["Unknown"])
                author = ", ".join(authors)
                
                # Avoid duplicates
                if not any(r["title"].lower() == title.lower() for r in recommendations):
                    recommendations.append({
                        "title": title,
                        "author": author,
                        "score": 10,  # Web results get a high priority score
                        "source": "Web"
                    })
    except Exception:
        pass

    # Sort by score
    return sorted(recommendations, key=lambda x: x['score'], reverse=True)


@api_view(['POST'])
def recommend_books(request):
    query = request.data.get('query', '').lower()
    if not query:
        return Response({"status": "error", "message": "query is required", "data": []}, status=400)
    recommendations = _build_recommendations(query)
    return Response({
        "status": "success",
        "data": recommendations[:7]
    })


@api_view(['GET'])
def related_books(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    seed_text = f"{book.title} {book.description}".strip().lower()
    recommendations = [
        item for item in _build_recommendations(seed_text)
        if item.get("title", "").lower() != book.title.lower()
    ]
    return Response({
        "status": "success",
        "book_id": book.id,
        "data": recommendations[:5]
    })


@api_view(['GET'])
def get_chat_history(request):
    rows = ChatHistory.objects.all()[:20]
    data = [
        {
            "id": row.id,
            "question": row.question,
            "answer": row.answer,
            "citations": row.citations,
            "created_at": row.created_at,
        }
        for row in rows
    ]
    return Response({"status": "success", "data": data})