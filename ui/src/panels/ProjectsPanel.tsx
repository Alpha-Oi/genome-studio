import { useEffect, useState } from "react";
import { createProject, deleteProject, listProjects } from "@/lib/projectsApi";
import type { Project } from "@/types/project";

interface Props {
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

export function ProjectsPanel({ selectedId, onSelect }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try {
      const items = await listProjects();
      setProjects(items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function add() {
    const name = newName.trim();
    if (!name || loading) return;
    setLoading(true);
    setError(null);
    try {
      const p = await createProject(name);
      setNewName("");
      setProjects((prev) => [p, ...prev]);
      onSelect(p.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete project?")) return;
    try {
      await deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      if (selectedId === id) onSelect(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  return (
    <div className="panel">
      <h2>Projects</h2>

      <div className="project-create">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New project name"
          onKeyDown={(e) => {
            if (e.key === "Enter") void add();
          }}
        />
        <button onClick={() => void add()} disabled={!newName.trim() || loading}>
          +
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {projects.length === 0 ? (
        <p>No projects yet.</p>
      ) : (
        <ul className="project-list">
          {projects.map((p) => (
            <li
              key={p.id}
              className={p.id === selectedId ? "selected" : ""}
              onClick={() => onSelect(p.id)}
            >
              <span className="pname">{p.name}</span>
              <button
                className="pdelete"
                onClick={(e) => {
                  e.stopPropagation();
                  void remove(p.id);
                }}
                title="Delete"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}