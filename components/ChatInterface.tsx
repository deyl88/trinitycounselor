"use client";

import { useEffect, useRef, useState } from "react";
import { clsx } from "clsx";

export type AgentMode = "private" | "relationship";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Props {
  agentMode: AgentMode;
  userId: string;
  placeholder?: string;
}

export default function ChatInterface({ agentMode, userId, placeholder }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // Auto-grow textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 140) + "px";
    }
  }, [input]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setStreamingContent("");

    const history = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history, agentMode, userId }),
      });

      if (!res.ok || !res.body) throw new Error("Request failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        full += chunk;
        setStreamingContent(full);
      }

      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "assistant", content: full },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "I'm here. Something went wrong on my end — can you try again?",
        },
      ]);
    } finally {
      setLoading(false);
      setStreamingContent("");
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const showWelcome = messages.length === 0 && !loading;

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 chat-scroll">
        {showWelcome && (
          <div className="text-center mt-16 px-6">
            <p className="text-stone-400 text-sm leading-relaxed">
              {agentMode === "private"
                ? "This is your private space. What's on your mind?"
                : "This is your shared space. What would you like to explore together?"}
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {/* Streaming response */}
        {loading && streamingContent && (
          <MessageBubble role="assistant" content={streamingContent} streaming />
        )}

        {/* Typing indicator (before any tokens arrive) */}
        {loading && !streamingContent && (
          <div className="flex items-end gap-2">
            <div className="bg-white border border-sand-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1.5 items-center h-4">
                <span className="w-1.5 h-1.5 bg-stone-400 rounded-full dot-pulse" />
                <span className="w-1.5 h-1.5 bg-stone-400 rounded-full dot-pulse" />
                <span className="w-1.5 h-1.5 bg-stone-400 rounded-full dot-pulse" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-sand-100 bg-sand-50 px-4 py-3">
        <div className="flex items-end gap-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={placeholder ?? "Say something…"}
            rows={1}
            className="flex-1 resize-none rounded-2xl bg-white border border-sand-200 px-4 py-3 text-sm text-stone-800 placeholder-stone-400 focus:outline-none focus:border-sand-400 transition leading-relaxed"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="w-10 h-10 rounded-full bg-sand-600 flex items-center justify-center transition active:scale-90 disabled:opacity-40 shrink-0"
          >
            <svg viewBox="0 0 24 24" className="w-4 h-4 fill-white" xmlns="http://www.w3.org/2000/svg">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
  role,
  content,
  streaming,
}: {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}) {
  const isUser = role === "user";
  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm",
          isUser
            ? "bg-sand-600 text-white rounded-br-sm"
            : "bg-white border border-sand-100 text-stone-800 rounded-bl-sm",
          streaming && "animate-pulse"
        )}
      >
        {content}
      </div>
    </div>
  );
}
