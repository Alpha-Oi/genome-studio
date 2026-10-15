import { useState } from "react";
import { fetchPlan } from "@/lib/api";
import { PlanCard } from "@/components/PlanCard";
import type { Plan } from "@/types/plan";

interface PlanEntry {
  id: number;
  plan: Plan;
}

export function ChatPanel() {
  const [text, setText] = useState("");
  const [plans, setPlans] = useState<PlanEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    try {
      const plan = await fetchPlan(trimmed);
      setPlans((prev) => [{ id: Date.now(), plan }, ...prev]);
      setText("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void submit();
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-input">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder='Например: "knockout gene lacZ in E. coli" (Ctrl+Enter — отправить)'
          rows={3}
          disabled={loading}
        />
        <button onClick={() => void submit()} disabled={loading || !text.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </div>

      {error && <div className="chat-error">Ошибка: {error}</div>}

      <div className="chat-results">
        {plans.length === 0 && !error && (
          <div className="chat-empty">
            Опиши цель — система предложит стратегию и план.
          </div>
        )}
        {plans.map((entry) => (
          <PlanCard key={entry.id} plan={entry.plan} />
        ))}
      </div>
    </div>
  );
}