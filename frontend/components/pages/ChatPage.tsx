"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { chatApi, documentsApi } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Document {
  id: number;
  title: string;
  status: string;
}

const GREETING =
  "Hi! I'm your study assistant. How can I help you today? You can ask me anything about your uploaded documents.";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("doc") ? Number(searchParams.get("doc")) : undefined;

  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: GREETING },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | undefined>(initialDocId);
  const [queryMode, setQueryMode] = useState("normal");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    documentsApi
      .list()
      .then((r) => setDocs(r.data.filter((d: Document) => d.status === "completed")));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    setLoading(true);

    const newMessages: Message[] = [...messages, { role: "user", content: question }];
    setMessages(newMessages);

    try {
      const history = newMessages
        .slice(1, -1) // exclude greeting and current question
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await chatApi.ask({
        question,
        document_id: selectedDoc,
        chat_history: history,
        query_mode: queryMode,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.answer },
      ]);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
        <div className="flex gap-3">
          <select
            value={selectedDoc ?? ""}
            onChange={(e) =>
              setSelectedDoc(e.target.value ? Number(e.target.value) : undefined)
            }
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All documents</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
          <select
            value={queryMode}
            onChange={(e) => setQueryMode(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="normal">Normal</option>
            <option value="eli5">Explain simply</option>
            <option value="practice">Practice problems</option>
            <option value="summary">Summary</option>
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-900 shadow-sm border border-gray-100"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-400 shadow-sm border border-gray-100 rounded-xl px-4 py-3 text-sm">
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask a question…"
          disabled={loading}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-5 py-3 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
