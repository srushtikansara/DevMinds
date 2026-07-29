"use client";

import { useEffect, useState } from "react";

type Match = {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  fit_score: number;
  fit_reason: string;
  applied: boolean;
  reviewed: boolean;
};

type Applied = {
  title: string;
  company: string;
  location: string;
  url: string;
  fit_score: number;
};

type PrepareResult = {
  job_title: string;
  company: string;
  apply_url: string;
  tailored_summary: string;
  highlighted_skills: string[];
  tailoring_notes: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

async function apiCall(path: string, method: string = "GET") {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function CareerMatchesPage() {
  const [tab, setTab] = useState<"matches" | "applied">("matches");
  const [matches, setMatches] = useState<Match[]>([]);
  const [applied, setApplied] = useState<Applied[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [prepared, setPrepared] = useState<PrepareResult | null>(null);
  const [preparedId, setPreparedId] = useState<string | null>(null);

  async function loadMatches() {
    setLoading(true);
    const data = await apiCall("/career/matches");
    setMatches(data.matches);
    setLoading(false);
  }

  async function loadApplied() {
    setLoading(true);
    const data = await apiCall("/career/applied");
    setApplied(data.applied);
    setLoading(false);
  }

  useEffect(() => {
    if (tab === "matches") loadMatches();
    else loadApplied();
  }, [tab]);

  async function handlePrepare(id: string) {
    setActionId(id);
    try {
      const result = await apiCall(`/career/matches/${id}/prepare`, "POST");
      setPrepared(result);
      setPreparedId(id);
    } catch {
      alert("Couldn't prepare this application. Check the backend is running.");
    }
    setActionId(null);
  }

  async function handleReject(id: string) {
    setActionId(id);
    try {
      await apiCall(`/career/matches/${id}/reject`, "POST");
      await loadMatches();
    } catch {
      alert("Couldn't reject this match.");
    }
    setActionId(null);
  }

  async function handleMarkAppliedDirect(id: string) {
    setActionId(id);
    try {
      await apiCall(`/career/matches/${id}/mark-applied`, "POST");
      await loadMatches();
    } catch {
      alert("Couldn't mark as applied.");
    }
    setActionId(null);
  }

  async function handleMarkApplied() {
    if (!preparedId) return;
    setActionId(preparedId);
    try {
      await apiCall(`/career/matches/${preparedId}/mark-applied`, "POST");
      await loadMatches();
      setPrepared(null);
    } catch {
      alert("Couldn't mark as applied.");
    }
    setActionId(null);
  }

  return (
    <main className="min-h-screen bg-[#0A0E14] text-[#E8EAED] px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Career</h1>
        <p className="text-sm text-[#8A9099] mb-6">
          Ranked by fit against your real, tracked skills.
        </p>

        <div className="flex gap-1 mb-8 border-b border-[#1C2128]">
          <button
            onClick={() => setTab("matches")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === "matches" ? "border-[#4C8DFF] text-[#E8EAED]" : "border-transparent text-[#8A9099]"
            }`}
          >
            Matches
          </button>
          <button
            onClick={() => setTab("applied")}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === "applied" ? "border-[#4C8DFF] text-[#E8EAED]" : "border-transparent text-[#8A9099]"
            }`}
          >
            Applied
          </button>
        </div>

        {loading && <p className="text-[#8A9099]">Loading...</p>}

        {!loading && tab === "matches" && (
          <div className="space-y-3">
            {matches.length === 0 && <p className="text-[#8A9099]">No matches yet.</p>}
            {matches.map((m) => (
              <div key={m.id} className="border border-[#1C2128] rounded-lg p-5 hover:border-[#2A3038] transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h2 className="font-medium text-[#E8EAED]">{m.title}</h2>
                    <p className="text-sm text-[#8A9099]">{m.company} · {m.location}</p>
                  </div>
                  <span className="font-mono text-sm text-[#4C8DFF]">{Math.round(m.fit_score * 100)}%</span>
                </div>

                <div className="h-1 bg-[#1C2128] rounded-full mb-3 overflow-hidden">
                  <div className="h-full bg-[#4C8DFF]" style={{ width: `${m.fit_score * 100}%` }} />
                </div>

                <p className="text-sm text-[#8A9099] mb-4">{m.fit_reason}</p>

                <div className="flex gap-2 text-sm items-center">
                  <a href={m.url} target="_blank" className="px-3 py-1.5 rounded-md bg-[#4C8DFF] text-[#0A0E14] font-medium">
                    View posting
                  </a>

                  {!m.reviewed && !m.applied && (
                    <>
                      <button onClick={() => handlePrepare(m.id)} disabled={actionId === m.id} className="px-3 py-1.5 rounded-md border border-[#2A3038] text-[#E8EAED] disabled:opacity-50">
                        {actionId === m.id ? "Working..." : "Prepare application"}
                      </button>
                      <button onClick={() => handleReject(m.id)} disabled={actionId === m.id} className="px-3 py-1.5 rounded-md border border-[#2A3038] text-[#8A9099] disabled:opacity-50">
                        Not interested
                      </button>
                    </>
                  )}

                  {m.reviewed && !m.applied && (
                    <button onClick={() => handleMarkAppliedDirect(m.id)} disabled={actionId === m.id} className="px-3 py-1.5 rounded-md border border-[#4C8DFF] text-[#4C8DFF] disabled:opacity-50">
                      {actionId === m.id ? "Marking..." : "Mark as applied"}
                    </button>
                  )}

                  {m.applied && <span className="text-xs text-[#4C8DFF] font-mono">✓ Applied</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && tab === "applied" && (
          <div className="space-y-2">
            {applied.length === 0 && (
              <p className="text-[#8A9099]">Nothing marked as applied yet.</p>
            )}
            {applied.map((a, i) => (
              <div key={i} className="border border-[#1C2128] rounded-lg p-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{a.title}</p>
                  <p className="text-sm text-[#8A9099]">{a.company} · {a.location}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm text-[#4C8DFF]">{Math.round(a.fit_score * 100)}%</span>
                  <a href={a.url} target="_blank" className="text-sm px-3 py-1.5 rounded-md border border-[#2A3038]">
                    View posting
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {prepared && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-8" onClick={() => setPrepared(null)}>
          <div className="bg-[#0F1419] border border-[#2A3038] rounded-lg p-8 max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-1">{prepared.job_title}</h2>
            <p className="text-sm text-[#8A9099] mb-6">{prepared.company}</p>

            <h3 className="text-xs uppercase tracking-wide text-[#4C8DFF] mb-2">Tailored summary</h3>
            <p className="text-sm mb-6">{prepared.tailored_summary}</p>

            <h3 className="text-xs uppercase tracking-wide text-[#4C8DFF] mb-2">Highlighted skills</h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {prepared.highlighted_skills.map((s) => (
                <span key={s} className="text-xs font-mono px-2 py-1 bg-[#1C2128] rounded">{s}</span>
              ))}
            </div>

            <h3 className="text-xs uppercase tracking-wide text-[#D9A441] mb-2">Honest gaps</h3>
            <p className="text-sm text-[#8A9099] mb-6">{prepared.tailoring_notes}</p>

            <div className="flex gap-2">
              <a href={prepared.apply_url} target="_blank" className="px-3 py-1.5 rounded-md bg-[#4C8DFF] text-[#0A0E14] font-medium text-sm">
                Apply now
              </a>
              <button onClick={handleMarkApplied} className="px-3 py-1.5 rounded-md border border-[#2A3038] text-sm">
                Mark as applied
              </button>
              <button onClick={() => setPrepared(null)} className="px-3 py-1.5 rounded-md border border-[#2A3038] text-sm">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}