"""ChromaDB persistence + MiniLM embeddings for book chunk RAG (used by ``ask_question``)."""
import os
from typing import List

try:
    import chromadb
except Exception:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

# Initialize ChromaDB in a persistent directory local to the books app
db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=db_path) if chromadb else None
collection = (
    chroma_client.get_or_create_collection(name="books_collection")
    if chroma_client
    else None
)

# Initialize Local Embedding Model
try:
    model = SentenceTransformer('all-MiniLM-L6-v2') if SentenceTransformer else None
except Exception as e:
    print("Failed to load sentence-transformer:", e)
    model = None

def add_to_vector_db(book_id, title, description):
    if not description or not model or not collection:
        return
    
    # Hybrid chunking with overlap improves recall in similarity search.
    paragraph_chunks = [c.strip() for c in description.split('\n') if len(c.strip()) > 10]
    chunks = paragraph_chunks if paragraph_chunks else []
    if not chunks:
        words = description.split()
        window = 90
        overlap = 25
        start = 0
        while start < len(words):
            chunk = " ".join(words[start:start + window]).strip()
            if chunk:
                chunks.append(chunk)
            if start + window >= len(words):
                break
            start += max(1, window - overlap)
    
    if not chunks:
        chunks = [description]
        
    for i, chunk in enumerate(chunks):
        doc_id = f"book_{book_id}_chunk_{i}"
        text_to_embed = f"Title: {title}\nDescription: {chunk}"
        
        embedding = model.encode(text_to_embed).tolist()
        
        collection.upsert(
            documents=[text_to_embed],
            embeddings=[embedding],
            metadatas=[{"book_id": book_id, "title": title}],
            ids=[doc_id]
        )

def query_vector_db(query_text, n_results=3) -> List[str]:
    if not model or not collection:
        return []
        
    embedding = model.encode(query_text).tolist()
    
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        if not results['documents'] or not results['documents'][0]:
            return []
        return results['documents'][0]
    except Exception as e:
        print("ChromaDB Query Error:", e)
        return []
