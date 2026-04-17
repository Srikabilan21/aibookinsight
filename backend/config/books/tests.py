"""
Lightweight API smoke tests (no external LLM required).

Run from `backend/config`:
  ..\\venv\\Scripts\\python.exe manage.py test books
"""
from django.test import TestCase
from rest_framework.test import APIClient


class CatalogApiTests(TestCase):
    """Basic JSON contract checks for catalog endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_list_books_returns_success(self):
        response = self.client.get("/api/books/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("status"), "success")
        self.assertIn("data", response.data)

    def test_chat_history_returns_success(self):
        response = self.client.get("/api/chat-history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("status"), "success")
        self.assertIn("data", response.data)


class RecommendApiTests(TestCase):
    """Recommendation endpoint validation."""

    def setUp(self):
        self.client = APIClient()

    def test_recommend_missing_query_returns_400(self):
        response = self.client.post("/api/recommend/", {}, format="json")
        self.assertEqual(response.status_code, 400)
