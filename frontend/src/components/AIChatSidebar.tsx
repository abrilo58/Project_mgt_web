"use client";

import { useCallback, useRef, useState } from "react";
import {
  sendChat,
  type ChatHistoryMessage,
} from "@/lib/api";

type AIChatSidebarProps = {
  onBoardUpdate?: () => void;
};

export function AIChatSidebar({ onBoardUpdate }: AIChatSidebarProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatHistoryMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      const el = listRef.current;
      if (!el) return;
      const top = el.scrollHeight;
      if (typeof el.scrollTo === "function") {
        el.scrollTo({ top, behavior: "smooth" });
      } else {
        el.scrollTop = top;
      }
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;

    const historyForApi = [...messages];
    setMessages((m) => [...m, { role: "user", content: text }]);
    setDraft("");
    setError(null);
    setLoading(true);
    scrollToBottom();

    try {
      const { message, board_updated } = await sendChat(text, historyForApi);
      setMessages((m) => [...m, { role: "assistant", content: message }]);
      if (board_updated) {
        onBoardUpdate?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat request failed");
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  return (
    <>
      <button
        type="button"
        data-testid="ai-chat-toggle"
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white px-5 py-3 text-sm font-semibold text-[var(--navy-dark)] shadow-[var(--shadow)] transition hover:border-[var(--accent-yellow)]"
        aria-expanded={open}
        aria-controls="ai-chat-panel"
      >
        <span
          className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]"
          aria-hidden
        />
        {open ? "Close assistant" : "AI assistant"}
      </button>

      {open ? (
        <aside
          id="ai-chat-panel"
          data-testid="ai-chat-panel"
          className="fixed bottom-24 right-6 z-40 flex h-[min(560px,calc(100vh-8rem))] w-[min(400px,calc(100vw-3rem))] flex-col rounded-3xl border border-[var(--stroke)] bg-white/95 shadow-[var(--shadow)] backdrop-blur"
        >
          <div className="border-b border-[var(--stroke)] px-5 py-4">
            <h2 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
              Board assistant
            </h2>
            <p className="mt-1 text-xs text-[var(--gray-text)]">
              Ask about your board or request changes. Uses your live Kanban
              data.
            </p>
          </div>

          <div
            ref={listRef}
            data-testid="ai-chat-messages"
            className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4"
          >
            {messages.length === 0 ? (
              <p className="text-center text-sm text-[var(--gray-text)]">
                No messages yet. Try &quot;What columns do I have?&quot;
              </p>
            ) : null}
            {messages.map((msg, i) => (
              <div
                key={`${i}-${msg.role}`}
                data-testid={`ai-chat-msg-${msg.role}`}
                className={
                  msg.role === "user"
                    ? "ml-8 rounded-2xl rounded-br-md bg-[var(--primary-blue)]/12 px-3 py-2 text-sm text-[var(--navy-dark)]"
                    : "mr-8 rounded-2xl rounded-bl-md border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
                }
              >
                {msg.content}
              </div>
            ))}
            {loading ? (
              <p
                data-testid="ai-chat-loading"
                className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
              >
                Thinking
              </p>
            ) : null}
          </div>

          {error ? (
            <p
              role="alert"
              className="mx-4 mb-2 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-800"
            >
              {error}
            </p>
          ) : null}

          <form
            onSubmit={handleSubmit}
            className="border-t border-[var(--stroke)] p-4"
          >
            <label htmlFor="ai-chat-input" className="sr-only">
              Message
            </label>
            <textarea
              id="ai-chat-input"
              data-testid="ai-chat-input"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={3}
              disabled={loading}
              placeholder="Message the assistant"
              className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none ring-[var(--primary-blue)] focus:ring-2 disabled:opacity-60"
            />
            <button
              type="submit"
              data-testid="ai-chat-send"
              disabled={loading || !draft.trim()}
              className="mt-3 w-full rounded-2xl bg-[var(--secondary-purple)] py-3 text-sm font-semibold text-white transition enabled:hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </aside>
      ) : null}
    </>
  );
}
