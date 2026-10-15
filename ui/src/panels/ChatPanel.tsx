import { useState } from "react";
import { fetchPlan } from "@/lib/api";
import { createExperiment } from "@/lib/projectsApi";
import { PlanCard } from "@/components/PlanCard";
import { GoalTemplates } from "@/components/GoalTemplates";
import type { Plan } from "@/types/plan";

interface Props {
  projectId: number | null;
  onPlanCreated?: () => void;
  onExperimentSaved?: () => void;
}

interface PlanEntry {
  id: number;
  plan: Plan;
}

export function ChatPanel({ projectId, onPlanCreated, onExperimentSaved }: Props) {
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
      const plan = await fetchPlan(trimmed, projectId ?? undefined);
      setPlans((prev) => [{ id: Date.now(), plan }, ...prev]);
      setText("");
      if (projectId !== null) {
        if (onPlanCreated) onPlanCreated();
        try {
          const title =
            plan.goal.intent +
            " " +
            plan.goal.target.gene +
            " in " +
            plan.goal.target.organism;
          await createExperiment(projectId, "plan", title, plan);
          if (onExperimentSaved) onExperimentSaved();
        } catch (persistErr) {
          console.warn("Failed to save experiment:", persistErr);
        }
      }
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

  function pickTemplate(t: string) {
    setText(t);
  }

  return (
    <div className="chat-panel">
      <GoalTemplates onPick={pickTemplate} />

      <div className="chat-input">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            projectId !== null
              ? 'Goal (will be saved to project): "knockout gene recA in E. coli"'
              : 'Example: "knockout gene lacZ in E. coli" - select a project to save'
          }
          rows={3}
          disabled={loading}
        />
        <button onClick={() => void submit()} disabled={loading || !text.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      <div className="chat-results">
        {plans.length === 0 && !error && (
          <div className="chat-empty">
            Describe a goal - the system will propose a strategy and a plan.
          </div>
        )}
        {plans.map((entry) => (
          <PlanCard key={entry.id} plan={entry.plan} />
        ))}
      </div>
    </div>
  );
}