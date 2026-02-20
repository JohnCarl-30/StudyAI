"use client";

import { useEffect, useState } from "react";
import { flashcardsApi } from "@/lib/api";

interface Flashcard {
  id: number;
  question: string;
  answer: string;
  difficulty_level: string;
  next_review_date: string;
  total_reviews: number;
  easiness_factor: number;
  repetitions: number;
}

type Quality = "again" | "hard" | "good" | "easy";

const QUALITY_BUTTONS: { label: string; value: Quality; color: string }[] = [
  { label: "Again", value: "again", color: "bg-red-100 text-red-700 hover:bg-red-200" },
  { label: "Hard", value: "hard", color: "bg-orange-100 text-orange-700 hover:bg-orange-200" },
  { label: "Good", value: "good", color: "bg-blue-100 text-blue-700 hover:bg-blue-200" },
  { label: "Easy", value: "easy", color: "bg-green-100 text-green-700 hover:bg-green-200" },
];

export default function FlashcardsPage() {
  const [dueCards, setDueCards] = useState<Flashcard[]>([]);
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [done, setDone] = useState(false);
  const [stats, setStats] = useState({ correct: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"menu" | "study">("menu");

  useEffect(() => {
    flashcardsApi.getDue().then((r) => {
      setDueCards(r.data.due_cards);
      setLoading(false);
    });
  }, []);

  const startSession = async () => {
    const res = await flashcardsApi.startSession();
    setSessionId(res.data.session_id);
    setCurrent(0);
    setFlipped(false);
    setDone(false);
    setStats({ correct: 0, total: 0 });
    setMode("study");
  };

  const handleReview = async (quality: Quality) => {
    const card = dueCards[current];
    const isCorrect = quality === "good" || quality === "easy";

    await flashcardsApi.review(card.id, quality);

    if (sessionId) {
      await flashcardsApi.recordReview(sessionId, isCorrect);
    }

    setStats((s) => ({
      correct: s.correct + (isCorrect ? 1 : 0),
      total: s.total + 1,
    }));

    if (current + 1 >= dueCards.length) {
      if (sessionId) await flashcardsApi.endSession(sessionId);
      setDone(true);
    } else {
      setCurrent((c) => c + 1);
      setFlipped(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>;
  }

  if (mode === "menu") {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Flashcards</h1>
        <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 max-w-md">
          <div className="text-4xl mb-3">🃏</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            {dueCards.length} card{dueCards.length !== 1 ? "s" : ""} due
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            {dueCards.length === 0
              ? "Great job! No cards due right now. Check back later."
              : "Review your due cards using spaced repetition."}
          </p>
          {dueCards.length > 0 && (
            <button
              onClick={startSession}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Start Study Session
            </button>
          )}
        </div>
      </div>
    );
  }

  if (done) {
    const accuracy = stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0;
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Session Complete!</h1>
        <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 max-w-md">
          <div className="text-4xl mb-4">🎉</div>
          <div className="space-y-2 text-sm text-gray-600 mb-6">
            <div className="flex justify-between"><span>Cards reviewed</span><span className="font-medium">{stats.total}</span></div>
            <div className="flex justify-between"><span>Correct</span><span className="font-medium text-green-600">{stats.correct}</span></div>
            <div className="flex justify-between"><span>Accuracy</span><span className="font-medium">{accuracy}%</span></div>
          </div>
          <button
            onClick={() => setMode("menu")}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Back to Menu
          </button>
        </div>
      </div>
    );
  }

  const card = dueCards[current];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Study Session</h1>
        <span className="text-sm text-gray-500">{current + 1} / {dueCards.length}</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-1.5 mb-8">
        <div
          className="bg-blue-600 h-1.5 rounded-full transition-all"
          style={{ width: `${((current) / dueCards.length) * 100}%` }}
        />
      </div>

      {/* Flashcard with flip */}
      <div className="flex flex-col items-center">
        <div
          className="w-full max-w-xl cursor-pointer"
          style={{ perspective: "1000px" }}
          onClick={() => setFlipped(!flipped)}
        >
          <div
            className="relative w-full transition-transform duration-500"
            style={{
              transformStyle: "preserve-3d",
              transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
              minHeight: "220px",
            }}
          >
            {/* Front */}
            <div
              className="absolute inset-0 bg-white rounded-2xl shadow-md border border-gray-100 p-8 flex flex-col justify-between"
              style={{ backfaceVisibility: "hidden" }}
            >
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">Question</span>
              <p className="text-lg font-medium text-gray-900 text-center">{card.question}</p>
              <p className="text-xs text-gray-400 text-center">Click to reveal answer</p>
            </div>
            {/* Back */}
            <div
              className="absolute inset-0 bg-blue-50 rounded-2xl shadow-md border border-blue-100 p-8 flex flex-col justify-between"
              style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
            >
              <span className="text-xs font-medium text-blue-400 uppercase tracking-wide">Answer</span>
              <p className="text-lg text-gray-900 text-center">{card.answer}</p>
              <p className="text-xs text-gray-400 text-center">How well did you know this?</p>
            </div>
          </div>
        </div>

        {flipped && (
          <div className="flex gap-3 mt-8">
            {QUALITY_BUTTONS.map(({ label, value, color }) => (
              <button
                key={value}
                onClick={() => handleReview(value)}
                className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-colors ${color}`}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        {!flipped && (
          <button
            onClick={() => setFlipped(true)}
            className="mt-8 px-6 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            Show Answer
          </button>
        )}
      </div>
    </div>
  );
}
