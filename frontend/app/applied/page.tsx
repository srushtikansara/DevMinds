"use client";

import { useEffect, useState } from "react";

type Applied = {
  title: string;
  company: string;
  location: string;
  url: string;
  fit_score: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

export default function AppliedJobsPage() {
  const [applied, setApplied] = useState<Applied[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/career/applied`, {
      headers: { Authorization: `Bearer ${API_KEY}` },
    })
      .then((res) => res.json())
      .then((data) => {
        setApplied(data.applied);
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Applied jobs</h1>
        <p className="text-sm text-[#8A9099] mb-8">
          Everything you've actually applied to, tracked in one place.
        </p>

        {loading && <p className="text-[#8A9099]">Loading...</p>}
        {!loading && applied.length === 0 && (
          <p className="text-[#8A9099]">
            Nothing marked as applied yet. Prepare and apply to a job from Career Matches, then confirm it there.
          </p>
        )}

        <div className="space-y-2">
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
      </div>
    </main>
  );
}