import { useRef, useState } from "react";
import { parseFastaContent, readFileAsText, type FastaRecord } from "@/lib/fastaApi";

interface Props {
  onLoad: (records: FastaRecord[]) => void;
  label?: string;
}

export function FastaUploadButton({ onLoad, label = "Upload FASTA" }: Props) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setBusy(true);
    setError(null);
    try {
      const text = await readFileAsText(file);
      const records = await parseFastaContent(text);
      onLoad(records);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <span className="fasta-upload">
      <button
        className="fasta-btn"
        type="button"
        onClick={() => fileRef.current?.click()}
        disabled={busy}
      >
        {busy ? "…" : label}
      </button>
      <input
        ref={fileRef}
        type="file"
        accept=".fasta,.fa,.fas,.fna,.txt"
        style={{ display: "none" }}
        onChange={(e) => void onChange(e)}
      />
      {error && <span className="fasta-error">{error}</span>}
    </span>
  );
}