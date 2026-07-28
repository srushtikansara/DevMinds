"use client";

import { useEffect, useState } from "react";

type Skill = { skill_name: string; proficiency_score: number; signal_count: number };
type Profile = {
  skill_summary: Skill[];
  activity_summary: {
    total_sessions: number;
    total_memories: number;
    total_skills_tracked: number;
    recent_highlights: { content: string; importance_score: number }[];
  };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

async function apiCall(path: string) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall("/profile").then((data) => {
      setProfile(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <main className="px-8 py-12 text-[#8A9099]">Loading your real profile...</main>;
  if (!profile) return <main className="px-8 py-12 text-[#8A9099]">No profile yet.</main>;

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Developer profile</h1>
        <p className="text-sm text-[#8A9099] mb-8">
          Built automatically from your real coding sessions.
        </p>

        <div className="grid grid-cols-3 gap-4 mb-10">
          <div className="border border-[#1C2128] rounded-lg p-4">
            <p className="font-mono text-2xl text-[#4C8DFF]">{profile.activity_summary.total_sessions}</p>
            <p className="text-xs text-[#8A9099] mt-1">Sessions captured</p>
          </div>
          <div className="border border-[#1C2128] rounded-lg p-4">
            <p className="font-mono text-2xl text-[#4C8DFF]">{profile.activity_summary.total_memories}</p>
            <p className="text-xs text-[#8A9099] mt-1">Memories</p>
          </div>
          <div className="border border-[#1C2128] rounded-lg p-4">
            <p className="font-mono text-2xl text-[#4C8DFF]">{profile.activity_summary.total_skills_tracked}</p>
            <p className="text-xs text-[#8A9099] mt-1">Skills tracked</p>
          </div>
        </div>

        <h2 className="font-medium mb-3">Top skills</h2>
        <div className="space-y-2 mb-10">
          {profile.skill_summary.slice(0, 8).map((s) => (
            <div key={s.skill_name} className="flex items-center gap-3">
              <span className="font-mono text-sm w-32 truncate">{s.skill_name}</span>
              <div className="flex-1 h-1.5 bg-[#1C2128] rounded-full overflow-hidden">
                <div className="h-full bg-[#4C8DFF]" style={{ width: `${s.proficiency_score * 100}%` }} />
              </div>
              <span className="text-xs text-[#8A9099] w-12 text-right">{Math.round(s.proficiency_score * 100)}%</span>
            </div>
          ))}
        </div>

        <h2 className="font-medium mb-3">Recent highlights</h2>
        <div className="space-y-2">
          {profile.activity_summary.recent_highlights.slice(0, 5).map((h, i) => (
            <div key={i} className="border border-[#1C2128] rounded-lg p-4 text-sm text-[#8A9099]">
              {h.content}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}