"use client";

import { useEffect, useState } from "react";

type Skill = { skill_name: string; proficiency_score: number; signal_count: number };
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

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([apiCall("/profile"), apiCall("/recommendations")]).then(([profile, recs]) => {
      setSkills(profile.skill_summary);
      setRecommendations(recs.recommendations);
      setLoading(false);
    });
  }, []);

  if (loading) return <main className="px-8 py-12 text-[#8A9099]">Loading...</main>;

  const maxProficiency = Math.max(...skills.map((s) => s.proficiency_score), 1);

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Skills</h1>
        <p className="text-sm text-[#8A9099] mb-8">
          Tracked from real events across all your connected tools.
        </p>

        <div className="flex items-end gap-2 h-48 mb-10 border-b border-[#1C2128] pb-2">
          {skills.map((s) => (
            <div key={s.skill_name} className="flex-1 flex flex-col items-center justify-end gap-2 group relative">
              <span className="text-xs font-mono text-[#4C8DFF] opacity-0 group-hover:opacity-100 transition-opacity">
                {Math.round(s.proficiency_score * 100)}%
              </span>
              <div
                className="w-full bg-[#4C8DFF] rounded-t"
                style={{ height: `${(s.proficiency_score / maxProficiency) * 100}%`, minHeight: "4px" }}
              />
              <span className="text-[10px] text-[#8A9099] rotate-45 origin-top-left whitespace-nowrap mt-1">
                {s.skill_name}
              </span>
            </div>
          ))}
        </div>

        <h2 className="font-medium mb-3">What to learn next</h2>
        <div className="space-y-2">
          {recommendations.map((r, i) => (
            <div key={i} className="border border-[#1C2128] rounded-lg p-4 flex justify-between items-center">
              <span className="font-mono text-sm">{r.content}</span>
              <span className="text-xs text-[#4C8DFF]">{Math.round(r.relevance_score * 100)}% relevance</span>
            </div>
          ))}
          {recommendations.length === 0 && (
            <p className="text-sm text-[#8A9099]">No recommendations yet.</p>
          )}
        </div>
      </div>
    </main>
  );
}