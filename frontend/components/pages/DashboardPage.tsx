"use client";

import { useEffect, useState } from "react";
import { flashcardsApi, documentsApi } from "@/lib/api";
import Link from "next/link";

interface Analytics {
  total_cards: number;
  total_reviews: number;
  overall_accuracy: number;
  due_today: number;
  mastered_cards: number;
  total_sessions: number;
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [docCount, setDocCount] = useState(0);

  useEffect(() => {
    flashcardsApi.analytics().then((r) => setAnalytics(r.data));
    documentsApi.list().then((r) => setDocCount(r.data.length));
  }, []);

  const stats = [
    { label: "Documents", value: docCount, icon: "📄", href: "/documents" },
    { label: "Flashcards", value: analytics?.total_cards ?? "—", icon: "🃏", href: "/flashcards" },
    { label: "Due Today", value: analytics?.due_today ?? "—", icon: "⏰", href: "/flashcards" },
    { label: "Accuracy", value: analytics ? `${analytics.overall_accuracy}%` : "—", icon: "🎯", href: "/flashcards" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon, href }) => (
          <Link
            key={label}
            href={href}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
          >
            <div className="text-2xl mb-2">{icon}</div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-3">Quick Actions</h2>
          <div className="space-y-2">
            <Link href="/documents" className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
              📤 Upload a PDF
            </Link>
            <Link href="/chat" className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
              💬 Ask a question
            </Link>
            <Link href="/flashcards" className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
              🃏 Study flashcards
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-3">Progress</h2>
          {analytics ? (
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Total reviews</span>
                <span className="font-medium">{analytics.total_reviews}</span>
              </div>
              <div className="flex justify-between">
                <span>Mastered cards</span>
                <span className="font-medium">{analytics.mastered_cards}</span>
              </div>
              <div className="flex justify-between">
                <span>Study sessions</span>
                <span className="font-medium">{analytics.total_sessions}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400">No data yet — start studying!</p>
          )}
        </div>
      </div>
    </div>
  );
}
