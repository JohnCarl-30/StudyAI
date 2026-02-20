import { Suspense } from "react";
import ChatPage from "@/components/pages/ChatPage";

export default function Page() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>}>
      <ChatPage />
    </Suspense>
  );
}
