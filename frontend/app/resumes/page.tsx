"use client";

import { useEffect, useState } from "react";

type Resume = {
    id:string;
    source:string;
    version:string;
    created_at:string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

async function apiCall(path:string,options: RequestInit = {}){
    const res= await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${API_KEY}`, ...options.headers },
  });
   if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function ResumePage(){
    const[resumes,setResumes]=useState<Resume[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    async function  loadResumes() {
     setLoading(true);
    const data = await apiCall("/resumes");
    setResumes(data.resumes);
    setLoading(false);
    }
    
    useEffect(() => {
        loadResumes();
    },[]);

    async function handleUpload(e:React.ChangeEvent<HTMLInputElement>){
        const file = e.target.files?.[0]
        if (!file) return;

        setUploading(true);
        setMessage(null);

        const formData = new FormData();
        formData.append("file", file);

        try{
            const res =   await fetch(`${API_URL}/resumes/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${API_KEY}` },
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      setMessage("Resume uploaded successfully.");
      await loadResumes();
        } catch (err){
            setMessage("Upload failed. Only .pdf and .docx files are supported")
        } finally {
            setUploading(false);
        }    
    }

    return (
        <main className="min-h-screen bg-[#0A0E14] text-[#E8EAED] px-8 py-12">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-2xl font-semibold mb-1">Resumes</h1>
                <p className="text-sm text-[#8A9099] mb-8">Upload an existing resume, or view what DevMind has generated from your real activity.
                </p>

                <div className="border border-[#1C2128] rounded-lg p-6 mb-8">
                    <h2 className="font-medium mb-3">Upload Resume</h2>
                    <input 
                    type = "file"
                    accept = ".pdf,.docx"
                    onChange={handleUpload}
                    disabled={uploading}
                    className="text-sm text-[#8A9099] file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-[#4C8DFF] file:text-[#0A0E14] file:font-medium file:cursor-pointer disabled:opacity-50"/>
                    {uploading && <p className="text-sm text-[#8A9099] mt-2">Uploading...</p>}
                    {message && <p className="text-sm text-[#4C8DFF] mt-2">{message}</p>}
                </div>
                <h2 className="font-medium mb-3">Your resumes</h2>

        {loading && <p className="text-[#8A9099]">Loading...</p>}
        {!loading && resumes.length === 0 && (
          <p className="text-[#8A9099]">No resumes yet. Upload one above.</p>
        )}
        <div className="space-y-2">
            {resumes.map((r) => (
                <div key={r.id} className="border border-[#1C2128] rounded-lg p-4 flex justify-between items-center">
                    <div>
                        <p className="font-mono text-sm text-[#4C8DFF] uppercase">{r.source}</p>
                        <p className="text-xs text-[#8A9099]">v{r.version} · {new Date(r.created_at).toLocaleDateString()}</p>
                    </div>
                    {r.source === "generated" && (
                
                 <a href={`${API_URL}/resumes/${r.id}/download`}
                  className="text-sm px-3 py-1.5 rounded-md border border-[#2A3038]"
                >
                  Download
                </a>
              )}
                </div>
            ))}

        </div>

            </div>
        </main>
    )
}
