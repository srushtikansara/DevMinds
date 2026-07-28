"use client";

import { useState } from "react";

type ReportSummary = {
  memories_this_week: { content: string; importance_score: number }[];
  skills_active_this_week: { skill_name: string; proficiency_score: number }[];
  open_recommendations: { content: string; relevance_score: number }[];
  totals: { memories: number; skills: number; recommendations: number };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

function getMostRecentMonday(): string {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().split("T")[0];
}

export default function ReportsPage() {
  const [weekStart, setWeekStart] = useState(getMostRecentMonday());
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  async function loadReport() {
    setLoading(true);
    setNotFound(false);
    setReport(null);
    try {
      const res = await fetch(`${API_URL}/reports/${weekStart}`, {
        headers: { Authorization: `Bearer ${API_KEY}` },
      });
      if (res.status === 404) {
        setNotFound(true);
        setLoading(false);
        return;
      }
      const data = await res.json();
      setReport(data.summary_json);
    } catch {
      setNotFound(true);
    }
    setLoading(false);
  }

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Weekly report</h1>
        <p className="text-sm text-[#8A9099] mb-8">
          A summary of everything real that happened this week.
        </p>

        <div className="flex gap-3 mb-8">
          <input
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
            className="bg-[#0F1419] border border-[#2A3038] rounded-md px-3 py-2 text-sm"
          />
          <button onClick={loadReport} className="px-3 py-1.5 rounded-md bg-[#4C8DFF] text-[#0A0E14] font-medium text-sm">
            Load report
          </button>
        </div>

        {loading && <p className="text-[#8A9099]">Loading...</p>}
        {notFound && (
          <p className="text-[#8A9099]">
            No report generated for the week starting {weekStart}.
          </p>
        )}

        {report && (
          <div className="space-y-10">
            <div className="grid grid-cols-3 gap-4">
              <div className="border border-[#1C2128] rounded-lg p-4">
                <p className="font-mono text-2xl text-[#4C8DFF]">{report.totals.memories}</p>
                <p className="text-xs text-[#8A9099] mt-1">Memories this week</p>
              </div>
              <div className="border border-[#1C2128] rounded-lg p-4">
                <p className="font-mono text-2xl text-[#4C8DFF]">{report.totals.skills}</p>
                <p className="text-xs text-[#8A9099] mt-1">Skills active</p>
              </div>
              <div className="border border-[#1C2128] rounded-lg p-4">
                <p className="font-mono text-2xl text-[#4C8DFF]">{report.totals.recommendations}</p>
                <p className="text-xs text-[#8A9099] mt-1">Open recommendations</p>
              </div>
            </div>

            <div>
              <h2 className="font-medium mb-3">This week's memories</h2>
              <div className="space-y-2">
                {report.memories_this_week.map((m, i) => (
                  <div key={i} className="border border-[#1C2128] rounded-lg p-4 text-sm text-[#8A9099]">
                    {m.content}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h2 className="font-medium mb-3">Skills active this week</h2>
              <div className="flex flex-wrap gap-2">
                {report.skills_active_this_week.map((s) => (
                  <span key={s.skill_name} className="text-xs font-mono px-2 py-1 bg-[#1C2128] rounded">
                    {s.skill_name} · {Math.round(s.proficiency_score * 100)}%
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h2 className="font-medium mb-3">Open recommendations</h2>
              <div className="space-y-2">
                {report.open_recommendations.map((r, i) => (
                  <div key={i} className="border border-[#1C2128] rounded-lg p-4 flex justify-between text-sm">
                    <span>{r.content}</span>
                    <span className="text-[#4C8DFF]">{Math.round(r.relevance_score * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}