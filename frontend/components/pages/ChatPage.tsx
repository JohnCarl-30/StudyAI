"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { documentsApi } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Document {
  id: number;
  title: string;
  status: string;
}

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1")
  .replace(/^http/, "ws");

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("doc") ? Number(searchParams.get("doc")) : undefined;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | undefined>(initialDocId);
  const [queryMode, setQueryMode] = useState("normal");
  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef<string>("");

  useEffect(() => {
    documentsApi.list().then((r) =>
      setDocs(r.data.filter((d: Document) => d.status === "completed"))
    );
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const connectWS = useCallback(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const ws = new WebSocket(`${WS_BASE}/ws/chat?token=${token}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "chunk") {
        pendingRef.current += data.text;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            updated[updated.length - 1] = { ...last, content: pendingRef.current };
          } else {
            updated.push({ role: "assistant", content: pendingRef.current });
          }
          return updated;
        });
      } else if (data.type === "done") {
        pendingRef.current = "";
        setStreaming(false);
      } else if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${data.message}` },
        ]);
        setStreaming(false);
      }
    };

    ws.onclose = () => { wsRef.current = null; };
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connectWS();
    return () => wsRef.current?.close();
  }, [connectWS]);

  const sendToWS = (question: string, history: Message[]) => {
    wsRef.current?.send(JSON.stringify({
      question,
      document_id: selectedDoc,
      query_mode: queryMode,
      chat_history: history.slice(-10).map((m) => ({ role: m.role, content: m.content })),
    }));
  };

  const send = () => {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput("");
    setStreaming(true);
    pendingRef.current = "";
    const newMessages: Message[] = [...messages, { role: "user", content: question }];
    setMessages(newMessages);

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWS();
      setTimeout(() => sendToWS(question, newMessages), 300);
    } else {
      sendToWS(question, newMessages);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
        <div className="flex gap-3">
          <select
            value={selectedDoc ?? ""}
            onChange={(e) => setSelectedDoc(e.target.value ? Number(e.target.value) : undefined)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All documents</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>{d.title}</option>
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
        {messages.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <div className="text-5xl mb-3">💬</div>
            <p>Ask a question about your documents</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-900 shadow-sm border border-gray-100"
            }`}>
              {msg.content}
              {streaming && i === messages.length - 1 && msg.role === "assistant" && (
                <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask a question…"
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={send}
          disabled={streaming || !input.trim()}
          className="px-5 py-3 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {streaming ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
