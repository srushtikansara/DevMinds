"use client";

import { useEffect, useState } from "react";

type Resume = { id: string; source: string; version: number; created_at: string };
type Role = { title: string; context: string; start_date: string; end_date: string };
type Education = { degree: string; institution: string; graduation_date: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

async function apiCall(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");

  const [education, setEducation] = useState<Education[]>([{ degree: "", institution: "", graduation_date: "" }]);
  const [roles, setRoles] = useState<Role[]>([{ title: "", context: "", start_date: "", end_date: "Present" }]);

  async function loadResumes() {
    setLoading(true);
    const data = await apiCall("/resumes");
    setResumes(data.resumes);
    setLoading(false);
  }

  useEffect(() => {
    loadResumes();
  }, []);

  async function handleDownload(resumeId: string) {
    const res = await fetch(`${API_URL}/resumes/${resumeId}/download`, {
      headers: { Authorization: `Bearer ${API_KEY}` },
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resume.docx";
    a.click();
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_URL}/resumes/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${API_KEY}` },
        body: formData,
      });
      if (!res.ok) throw new Error(`${res.status}`);
      setMessage("Resume uploaded successfully.");
      await loadResumes();
    } catch {
      setMessage("Upload failed. Only .pdf and .docx files are supported.");
    } finally {
      setUploading(false);
    }
  }

  function updateEducation(index: number, field: keyof Education, value: string) {
    const updated = [...education];
    updated[index] = { ...updated[index], [field]: value };
    setEducation(updated);
  }

  function updateRole(index: number, field: keyof Role, value: string) {
    const updated = [...roles];
    updated[index] = { ...updated[index], [field]: value };
    setRoles(updated);
  }

  async function handleGenerate() {
    setUploading(true);
    setMessage(null);
    try {
      await apiCall("/resumes/generate", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          phone,
          linkedin_url: linkedinUrl,
          portfolio_url: portfolioUrl,
          education,
          roles,
        }),
      });
      setMessage("Resume generation started — refresh in a few seconds.");
      setShowForm(false);
    } catch {
      setMessage("Generation failed. Check all fields are filled in.");
    } finally {
      setUploading(false);
    }
  }

  const inputClass = "bg-[#0F1419] border border-[#2A3038] rounded-md px-3 py-2 text-sm w-full";

  return (
    <main className="min-h-screen px-8 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Resumes</h1>
        <p className="text-sm text-[#8A9099] mb-8">
          Upload an existing resume, or generate one from your real activity.
        </p>

        <div className="border border-[#1C2128] rounded-lg p-6 mb-4">
          <h2 className="font-medium mb-3">Upload a resume</h2>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleUpload}
            disabled={uploading}
            className="text-sm text-[#8A9099] file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-[#4C8DFF] file:text-[#0A0E14] file:font-medium file:cursor-pointer disabled:opacity-50"
          />
        </div>

        <div className="border border-[#1C2128] rounded-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-medium">Generate from my activity</h2>
            <button onClick={() => setShowForm(!showForm)} className="text-sm px-3 py-1.5 rounded-md border border-[#2A3038]">
              {showForm ? "Cancel" : "Start"}
            </button>
          </div>

          {showForm && (
            <div className="space-y-6">
              <div>
                <p className="text-xs uppercase tracking-wide text-[#4C8DFF] mb-2">Contact</p>
                <div className="grid grid-cols-2 gap-3">
                  <input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputClass} />
                  <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} />
                  <input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} className={inputClass} />
                  <input placeholder="LinkedIn URL" value={linkedinUrl} onChange={(e) => setLinkedinUrl(e.target.value)} className={inputClass} />
                  <input placeholder="Portfolio / GitHub URL" value={portfolioUrl} onChange={(e) => setPortfolioUrl(e.target.value)} className={inputClass} />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-xs uppercase tracking-wide text-[#4C8DFF]">Education</p>
                  <button
                    onClick={() => setEducation([...education, { degree: "", institution: "", graduation_date: "" }])}
                    className="text-xs px-2 py-1 rounded border border-[#2A3038]"
                  >
                    + Add education
                  </button>
                </div>
                {education.map((edu, i) => (
                  <div key={i} className="grid grid-cols-3 gap-3 mb-2">
                    <input placeholder="Degree" value={edu.degree} onChange={(e) => updateEducation(i, "degree", e.target.value)} className={inputClass} />
                    <input placeholder="Institution" value={edu.institution} onChange={(e) => updateEducation(i, "institution", e.target.value)} className={inputClass} />
                    <input placeholder="Graduation date" value={edu.graduation_date} onChange={(e) => updateEducation(i, "graduation_date", e.target.value)} className={inputClass} />
                  </div>
                ))}
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <p className="text-xs uppercase tracking-wide text-[#4C8DFF]">Experience / Projects</p>
                  <button
                    onClick={() => setRoles([...roles, { title: "", context: "", start_date: "", end_date: "Present" }])}
                    className="text-xs px-2 py-1 rounded border border-[#2A3038]"
                  >
                    + Add experience
                  </button>
                </div>
                <p className="text-xs text-[#8A9099] mb-2">
                  Add each real project or role separately — DevMind will pull matching work from your tracked memories for each one.
                </p>
                {roles.map((role, i) => (
                  <div key={i} className="grid grid-cols-4 gap-3 mb-2">
                    <input placeholder="Title" value={role.title} onChange={(e) => updateRole(i, "title", e.target.value)} className={inputClass} />
                    <input placeholder="Context (Company / Personal Project)" value={role.context} onChange={(e) => updateRole(i, "context", e.target.value)} className={inputClass} />
                    <input placeholder="Start date" value={role.start_date} onChange={(e) => updateRole(i, "start_date", e.target.value)} className={inputClass} />
                    <input placeholder="End date" value={role.end_date} onChange={(e) => updateRole(i, "end_date", e.target.value)} className={inputClass} />
                  </div>
                ))}
              </div>

              <p className="text-xs text-[#8A9099]">
                Skills are pulled automatically from your real tracked proficiency — no need to enter them manually.
              </p>

              <button onClick={handleGenerate} disabled={uploading} className="px-3 py-1.5 rounded-md bg-[#4C8DFF] text-[#0A0E14] font-medium text-sm disabled:opacity-50">
                {uploading ? "Generating..." : "Generate resume"}
              </button>
            </div>
          )}
        </div>

        {message && <p className="text-sm text-[#4C8DFF] mb-6">{message}</p>}

        <h2 className="font-medium mb-3">Your resumes</h2>
        {loading && <p className="text-[#8A9099]">Loading...</p>}
        <div className="space-y-2">
          {resumes.map((r) => (
            <div key={r.id} className="border border-[#1C2128] rounded-lg p-4 flex justify-between items-center">
              <div>
                <p className="font-mono text-sm text-[#4C8DFF] uppercase">{r.source}</p>
                <p className="text-xs text-[#8A9099]">v{r.version} · {new Date(r.created_at).toLocaleDateString()}</p>
              </div>
              {r.source === "generated" && (
                <button onClick={() => handleDownload(r.id)} className="text-sm px-3 py-1.5 rounded-md border border-[#2A3038]">
                  Download
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}