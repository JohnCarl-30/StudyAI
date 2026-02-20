import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
});

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// --- Auth ---
export const authApi = {
  signup: (email: string, password: string, username?: string) =>
    api.post("/auth/signup", { email, password, username }),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  me: () => api.get("/auth/me"),
};

// --- Documents ---
export const documentsApi = {
  list: () => api.get("/documents/"),
  upload: (file: File, title?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return api.post("/documents/upload", form);
  },
  get: (id: number) => api.get(`/documents/${id}`),
  delete: (id: number) => api.delete(`/documents/${id}`),
  reprocess: (id: number) => api.post(`/documents/${id}/reprocess`),
};

// --- Chat ---
export const chatApi = {
  ask: (payload: {
    question: string;
    document_id?: number;
    chat_history?: { role: string; content: string }[];
    query_mode?: string;
  }) => api.post("/chat/ask", payload),
  search: (query: string, document_id?: number) =>
    api.post("/chat/search", { query, document_id, k: 5 }),
};

// --- Flashcards ---
export const flashcardsApi = {
  list: (document_id?: number) =>
    api.get("/flashcards/", { params: { document_id } }),
  getDue: (document_id?: number) =>
    api.get("/flashcards/due", { params: { document_id } }),
  create: (data: {
    question: string;
    answer: string;
    document_id?: number;
    difficulty_level?: string;
  }) => api.post("/flashcards/", data),
  review: (id: number, quality: "again" | "hard" | "good" | "easy") =>
    api.post(`/flashcards/${id}/review`, { quality }),
  delete: (id: number) => api.delete(`/flashcards/${id}`),
  startSession: () => api.post("/flashcards/sessions/start"),
  endSession: (sessionId: number) =>
    api.post(`/flashcards/sessions/${sessionId}/end`),
  recordReview: (sessionId: number, correct: boolean) =>
    api.patch(`/flashcards/sessions/${sessionId}/record`, null, {
      params: { correct },
    }),
  analytics: () => api.get("/flashcards/analytics/summary"),
};
