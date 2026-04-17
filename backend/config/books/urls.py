from django.urls import path
from .views import (
    get_books,
    get_book_detail,
    add_book,
    scrape_books,
    recommend_books,
    related_books,
    book_summary,
    ask_question,
    sentiment_analysis,
    classify_genre,
    analyze_text,
    get_chat_history,
)

urlpatterns = [
    path('books/', get_books),
    path('books/<int:book_id>/', get_book_detail),
    path('add-book/', add_book),
    path('scrape-books/', scrape_books),
    path('recommend/', recommend_books),
    path('books/<int:book_id>/related/', related_books),
    path('summary/<int:book_id>/', book_summary),
    path('ask/', ask_question),
    path('chat-history/', get_chat_history),
    path('sentiment/', sentiment_analysis),
    path('genre/', classify_genre),
    path('analyze/', analyze_text),
]