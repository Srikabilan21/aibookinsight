import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
  // Backend may wait several minutes for a slow local LLM (LM Studio) plus RAG work.
  timeout: 300000,
});

export default api;
