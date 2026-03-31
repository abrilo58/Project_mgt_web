"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { KanbanBoard } from "@/components/KanbanBoard";

export default function Home() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [boardRefreshNonce, setBoardRefreshNonce] = useState<
    number | undefined
  >(undefined);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          router.replace("/login");
        } else {
          setReady(true);
        }
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  const handleLogout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    router.replace("/login");
  };

  if (!ready) return null;
  return (
    <ErrorBoundary>
      <KanbanBoard
        boardRefreshNonce={boardRefreshNonce}
        onLogout={handleLogout}
      />
      <AIChatSidebar
        onBoardUpdate={() => setBoardRefreshNonce(Date.now())}
      />
    </ErrorBoundary>
  );
}
