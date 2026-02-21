"use client";

import { useEffect, useRef, useState } from "react";
import { documentsApi } from "@/lib/api";
import Link from "next/link";

interface Document {
  id: number;
  title: string;
  filename: string;
  status: string;
  page_count: number | null;
  chunk_count: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => documentsApi.list().then((r) => setDocs(r.data));

  useEffect(() => { load(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await documentsApi.upload(file, file.name.replace(".pdf", ""));
      await load();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed. Please try again.";
      setUploadError(detail);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this document?")) return;
    await documentsApi.delete(id);
    setDocs((d) => d.filter((doc) => doc.id !== id));
  };

  const statusColor: Record<string, string> = {
    completed: "text-green-600 bg-green-50",
    processing: "text-yellow-600 bg-yellow-50",
    pending: "text-gray-500 bg-gray-100",
    failed: "text-red-600 bg-red-50",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <label className="cursor-pointer px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
          {uploading ? "Uploading…" : "📤 Upload PDF"}
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </div>

      {uploadError && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <strong>Upload error:</strong> {uploadError}
        </div>
      )}

      {docs.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-3">📄</div>
          <p>No documents yet. Upload a PDF to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {docs.map((doc) => (
            <div key={doc.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{doc.title}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {doc.page_count ? `${doc.page_count} pages · ` : ""}
                  {doc.chunk_count} chunks ·{" "}
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor[doc.status] ?? "text-gray-500"}`}>
                  {doc.status}
                </span>
                {doc.status === "completed" && (
                  <Link
                    href={`/chat?doc=${doc.id}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Chat
                  </Link>
                )}
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="text-xs text-red-500 hover:underline"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
