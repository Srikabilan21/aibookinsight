# 📚 BookInsight (AI Book Intelligence Platform)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-blue)
![AI](https://img.shields.io/badge/AI-RAG-orange)

A full-stack AI-powered web application that allows users to explore books and interact with an intelligent assistant.

---

## 🚀 Features

- 📊 Sentiment Analysis  
- 🎭 Genre Classification  
- 💬 RAG-based Q&A (BookInsight Chat)  
- 📚 Book Dashboard  
- 🔎 Related Book Recommendations  
- 🧠 AI-powered insights  

---

## 🧠 How it works

1. User asks a question  
2. System retrieves relevant book data (ChromaDB)  
3. Fetches additional context (Google Books + Open Library)  
4. Sends combined context to local LLM (LM Studio)  
5. Returns an intelligent response  

---

## 🖼️ UI Screenshots

![Dashboard](assets/screenshots/dashboardpagefirst.png)
![Book Detail](assets/screenshots/viewdetailspage.png)
![Q&A Chat](assets/screenshots/qa.png)
![Chat History](assets/screenshots/chathist.png)
![Welcome](assets/screenshots/welcomepage.png)

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|------------|
| Backend | Django + Django REST Framework |
| Database | SQLite |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| Frontend | React + Vite + Tailwind CSS |
| Automation | Selenium |
| LLM | LM Studio |

---

## ⚙️ Setup Instructions

### 🔹 Prerequisites

- Python 3.10+
- Node.js 20+
- LM Studio (running on `http://127.0.0.1:1234`)

---

### 🔹 Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd config
python manage.py migrate
python manage.py runserver
```
Backend URL:
http://127.0.0.1:8000/api

#### 🔹 Frontend Setup
```bash
cd frontend-react
npm install
npm run dev
```
Frontend URL:
http://localhost:5173

#### 🔹 LM Studio Setup
Open LM Studio
Download a chat model (e.g., Llama 3)
Start server at:
http://127.0.0.1:1234


#### 🔌 API Documentation
📚 Books
Method	Endpoint	Description
GET	/books/	Get all books
GET	/books/<id>/	Get book details
POST	/add-book/	Add a book
GET	/books/<id>/related/	Related books
GET	/summary/<id>/	Book summary


### 💬 Q&A (RAG)
Method	Endpoint
POST	/ask/
GET	/chat-history/
Sample Request
{
  "question": "What is the theme of this book?",
  "conversation": []
}


### 🧠 AI Features
Endpoint	Description
/recommend/	Book recommendations
/sentiment/	Sentiment analysis
/genre/	Genre classification
/analyze/	AI-based analysis


### 💡 Sample Questions & Answers

Q1: What is the Ramayana about?
A: A concise explanation of its story, themes, and characters.

Q2: Recommend books like Sapiens
A: Suggests similar historical and idea-based books.

Q3: Recommend short fiction books
A: Provides a list of short novels under 300 pages.


### 🧪 Testing Samples

Check the samples/ folder for:

API request examples
JSON payloads for testing


### 📦 Requirements

All dependencies are listed in:
backend/requirements.txt

### 📂 Project Structure
aibookinsight/
├── backend/
├── frontend-react/
├── assets/screenshots/
├── samples/
└── README.md

### 🔐 Security Note
Sensitive data like API keys are stored in .env and are not committed.

### 🔮 Future Improvements
-Add user authentication
-Improve UI/UX animations
-Deploy to cloud (Render/Vercel)