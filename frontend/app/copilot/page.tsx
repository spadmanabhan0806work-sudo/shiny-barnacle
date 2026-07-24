"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send, User } from "lucide-react";
import { PageShell } from "@/components/layout/page-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api, type ChatMessage } from "@/lib/api";

const SUGGESTED_PROMPTS = [
  "Which suppliers are delayed?",
  "Show high risk vendors.",
  "What inventory is low?",
  "Show recent purchase orders.",
  "Warehouse capacity status?",
];

export default function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello! I'm your Procurement Copilot. Ask me about suppliers, orders, shipments, or inventory." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [followups, setFollowups] = useState<string[]>(SUGGESTED_PROMPTS);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: text };
    const history = messages.filter((m) => m.role !== "system");
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.copilotChat(text, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      if (res.suggested_followups.length) setFollowups(res.suggested_followups);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I couldn't process that request. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell title="Procurement Copilot" description="AI assistant for supply chain and procurement queries">
      <div className="mx-auto max-w-4xl space-y-3 sm:space-y-4">
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {followups.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="rounded-full border border-border bg-muted/30 px-2.5 py-1 text-xs hover:bg-primary/10 hover:border-primary/30 transition-colors text-left"
            >
              {prompt}
            </button>
          ))}
        </div>

        <Card className="h-[calc(100vh-240px)] sm:h-[calc(100vh-280px)] min-h-[400px] flex flex-col">
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            <ScrollArea className="flex-1 p-3 sm:p-6">
              <div className="space-y-4">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-2 sm:gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                    {msg.role === "assistant" && (
                      <div className="flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-primary/20">
                        <Bot className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`max-w-[88%] sm:max-w-[80%] rounded-lg px-3.5 py-2.5 sm:px-4 sm:py-3 text-xs sm:text-sm whitespace-pre-wrap ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted/50 border border-border/50"
                      }`}
                    >
                      {msg.content}
                    </div>
                    {msg.role === "user" && (
                      <div className="flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                        <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-2 sm:gap-3">
                    <div className="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full bg-primary/20">
                      <Bot className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
                    </div>
                    <div className="rounded-lg bg-muted/50 px-4 py-2.5 text-xs sm:text-sm text-muted-foreground">
                      <span className="inline-flex gap-1">
                        <span className="animate-bounce">.</span>
                        <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
                        <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
                      </span>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>

            <div className="border-t border-border p-3 sm:p-4 flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
                placeholder="Ask about suppliers, orders, inventory..."
                disabled={loading}
                className="text-xs sm:text-sm"
              />
              <Button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} size="icon" className="shrink-0 sm:w-auto sm:px-4">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}

