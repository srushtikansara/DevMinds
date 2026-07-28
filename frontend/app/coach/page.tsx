"use client";

import { useEffect, useState } from "react";

type Recommendation = { content: string; relevance_score: number; type: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

async function apiCall(path: string) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function CoachPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall("/recommendations").then((data) => {
      setRecommendations(data.recommendations);
      setLoading(false);
    });
  }, []);

  if (loading) return <main className="px-8 py-12 text-[#8A9099]">Checking in on your progress...</main>;

  const top = recommendations[0];
  const rest = recommendations.slice(1);

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Your coach</h1>
        <p className="text-sm text-[#8A9099] mb-10">
          Based on everything DevMind has tracked from your real work.
        </p>

        {top && (
          <div className="border border-[#4C8DFF] rounded-lg p-8 mb-10">
            <p className="text-xs uppercase tracking-wide text-[#4C8DFF] mb-3">Focus this week</p>
            <h2 className="text-xl font-mono mb-2">{top.content}</h2>
            <p className="text-sm text-[#8A9099]">
              This is the highest-relevance gap identified from your current skill combination —
              {" "}{Math.round(top.relevance_score * 100)}% confidence this is the right next step.
            </p>
          </div>
        )}

        {rest.length > 0 && (
          <>
            <p className="text-sm text-[#8A9099] mb-3">Also worth keeping in mind</p>
            <div className="space-y-2">
              {rest.map((r, i) => (
                <div key={i} className="border border-[#1C2128] rounded-lg p-4 flex justify-between text-sm">
                  <span className="font-mono">{r.content}</span>
                  <span className="text-[#8A9099]">{Math.round(r.relevance_score * 100)}%</span>
                </div>
              ))}
            </div>
          </>
        )}

        {recommendations.length === 0 && (
          <p className="text-[#8A9099]">
            No recommendations yet — once you've tracked a few skills, your coach will have real, specific guidance here.
          </p>
        )}
      </div>
    </main>
  );
}