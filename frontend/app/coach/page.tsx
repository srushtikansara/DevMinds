"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";

// Types matching the existing backend API structures
type Skill = { skill_name: string; proficiency_score: number; signal_count: number };
type Profile = {
  user_id: string;
  skill_summary: Skill[];
  activity_summary: {
    total_sessions: number;
    total_memories: number;
    total_skills_tracked: number;
    recent_highlights: { content: string; importance_score: number }[];
  };
};

type Recommendation = { content: string; relevance_score: number; type: string };

type CareerMatch = {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  fit_score: number;
  fit_reason: string;
};

type Message = {
  id: string;
  sender: "user" | "coach";
  text: string;
  timestamp: Date;
};

type InterviewQuestion = {
  question: string;
  idealKeywords: string[];
  sampleAnswer: string;
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

export default function CoachPage() {
  // Global dashboard state
  const [profile, setProfile] = useState<Profile | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [careerMatches, setCareerMatches] = useState<CareerMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"coach" | "career" | "interview">("coach");

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Roadmaps Accordion State
  const [expandedRoadmap, setExpandedRoadmap] = useState<number | null>(0);

  // Selected Career Match for detail analysis
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Interview Simulator State
  const [interviewJob, setInterviewJob] = useState<CareerMatch | null>(null);
  const [interviewStep, setInterviewStep] = useState<number>(-1); // -1 = not started, 0, 1, 2 = question index, 3 = completed
  const [interviewAnswers, setInterviewAnswers] = useState<string[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [feedbackHistory, setFeedbackHistory] = useState<string[]>([]);
  const [idealAnswersHistory, setIdealAnswersHistory] = useState<string[]>([]);

  // Study Tracker Goals (Local State)
  const [weeklyGoal, setWeeklyGoal] = useState("Complete 3 learning nodes");
  const [studyStreak, setStudyStreak] = useState(4); // Simulated streak
  const [completedGoals, setCompletedGoals] = useState<string[]>([]);

  // Load backend data
  useEffect(() => {
    Promise.all([
      apiCall("/profile").catch(() => null),
      apiCall("/recommendations").catch(() => ({ recommendations: [] })),
      apiCall("/career/matches").catch(() => ({ matches: [] })),
    ])
      .then(([profileData, recData, careerData]) => {
        setProfile(profileData);
        setRecommendations(recData?.recommendations || []);
        
        const matches = careerData?.matches || [];
        setCareerMatches(matches);
        if (matches.length > 0) {
          setSelectedJobId(matches[0].id);
        }
        setLoading(false);

        // Initialize Chat greeting
        const name = profileData?.skill_summary?.[0]?.skill_name || "Python";
        setMessages([
          {
            id: "greeting",
            sender: "coach",
            text: `👋 Hello! I am your **DevMind Learning Coach**. I have analyzed your tracked developer profile (including **${name}** and other skills). \n\nI am connected to your backend workspace logs. You can ask me to **search your coding history** or guide you on learning gaps. What would you like to achieve today?`,
            timestamp: new Date(),
          },
        ]);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // Auto scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0A0E14] flex items-center justify-center text-[#8A9099]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-[#4C8DFF] border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-mono tracking-wider animate-pulse">SYNCHRONIZING WITH AI MENTOR...</p>
        </div>
      </main>
    );
  }

  // Helper: Dynamically generated smart learning schedules based on recommendation title
  function getRoadmapSteps(content: string) {
    const tech = content.split(" ").slice(-1)[0] || content;
    return [
      {
        week: "Week 1: Core Fundamentals",
        desc: `Learn the setup, basic syntax, and CLI ecosystem for ${tech}. Review official documentation quickstarts.`,
        resources: [`Official ${tech} Documentation`, "MDN Web Docs"],
      },
      {
        week: "Week 2: Component Architecture & Database Integration",
        desc: `Build small mock projects. Connect ${tech} to a backend db or static data model and understand data flows.`,
        resources: ["Awesome Github Curated Resource Repository", "DevMind Coding Sandbox"],
      },
      {
        week: "Week 3: Advanced Optimization & Middleware",
        desc: `Explore caching, performance tuning, secure configurations, and multi-threaded processing in ${tech}.`,
        resources: [`Advanced ${tech} Optimization Guide`, "Medium Tech Blogs"],
      },
      {
        week: "Week 4: Real-World Signals Verification",
        desc: `Write code using ${tech} in your workspaces. DevMind will capture coding session events and index this skill!`,
        resources: ["DevMind Profile Analyzer Tools"],
      },
    ];
  }

  // Helper: Generate simulated technical answers for mock interviews
  function getInterviewQuestions(jobTitle: string): InterviewQuestion[] {
    const isFrontend = /front|react|design|css|javascript/i.test(jobTitle);
    const isBackend = /back|python|django|sql|node|database|api/i.test(jobTitle);

    if (isFrontend) {
      return [
        {
          question: "Can you explain the difference between state management in a client-side library like React vs standard server-rendered HTML components, and when you'd use context selectors?",
          idealKeywords: ["re-render", "global state", "prop drilling", "context provider", "performance"],
          sampleAnswer: "Client-side state management coordinates interactive UI events without roundtrips to the server. Context API is suitable for simple themes or user auth, but high-frequency updates require custom selectors, Zustand, or Redux to avoid unnecessary re-renders of the DOM tree.",
        },
        {
          question: "How do you optimize page rendering speeds for a complex Next.js application that renders hundreds of dynamic listings?",
          idealKeywords: ["caching", "lazy loading", "server components", "suspense", "image optimization"],
          sampleAnswer: "I would use React Server Components (RSC) to fetch data on the server, implement infinite scroll with Dynamic Imports (lazy loading), compress visuals using the Next.js Image component, and leverage Redis or fetch caching headers for repeat data requests.",
        },
        {
          question: "Explain your process for ensuring consistent cross-browser styling and accessible layout forms.",
          idealKeywords: ["flexbox", "grid", "aria labels", "semantic html", "postcss"],
          sampleAnswer: "I write semantic HTML structure (like <main> and <section>), add descriptive ARIA labels for assistive technologies, use flexbox/grid for responsive alignments, and use PostCSS/Tailwind autoprefixes to guarantee compatibility across older browsers.",
        },
      ];
    } else if (isBackend) {
      return [
        {
          question: "How do you design a high-throughput API endpoint to prevent database write bottlenecks and handle spike requests?",
          idealKeywords: ["caching", "rate limiting", "message queue", "indexing", "connection pooling"],
          sampleAnswer: "I implement API Gateway rate-limiting to block requests, a memory cache (like Redis) for read queries, database connection pooling (like SQLAlchemy's pool size), and pass heavy write queries to an asynchronous message broker (like Celery/RabbitMQ) for deferred background workers.",
        },
        {
          question: "What is database indexing, and how do you decide which database columns should be indexed?",
          idealKeywords: ["b-tree", "lookup latency", "foreign key", "where clause", "write overhead"],
          sampleAnswer: "An index is a data structure (commonly B-Tree) that speeds up lookup queries. I index columns that are frequently used in WHERE clauses, JOIN conditions, and foreign keys. I avoid indexing every column because it creates substantial write overhead on INSERT/UPDATE operations.",
        },
        {
          question: "Explain the difference between synchronous and asynchronous task execution, and when you would use each in Python.",
          idealKeywords: ["event loop", "non-blocking", "io bound", "cpu bound", "asyncio"],
          sampleAnswer: "Synchronous execution blocks subsequent code until the current line finishes. Asynchronous execution yields execution during slow I/O tasks. I use async/await for networks, file reads, and API integrations, while using multi-processing or task queues for CPU-heavy computing.",
        },
      ];
    } else {
      return [
        {
          question: "Can you explain your workflow for debugging a server crash or a performance regression in a production software service?",
          idealKeywords: ["logs", "stack trace", "profiler", "git bisect", "metrics"],
          sampleAnswer: "I check APM metrics for CPU/memory exhaustion, scan stderr logs to locate the fatal stack trace, use local profilers (like cProfile) to identify bottlenecks, and use git bisect to isolate the commit that introduced the performance regression.",
        },
        {
          question: "How do you handle API versioning and ensure backward compatibility for third-party integrations?",
          idealKeywords: ["url path", "deprecation headers", "semantic versioning", "dto models"],
          sampleAnswer: "I version via the URL path (e.g., /api/v1) and keep old models active when adding new parameters. I write data-transfer object (DTO) models for conversion and supply custom headers warning clients about upcoming deprecations.",
        },
        {
          question: "What is your approach to writing modular, testable code in a team development environment?",
          idealKeywords: ["dependency injection", "solid principles", "unit tests", "mocking", "interfaces"],
          sampleAnswer: "I build decoupled structures using Dependency Injection, write clear interfaces so components can be easily mocked, adhere strictly to SOLID principles, and enforce code coverage through automated unit tests in CI/CD.",
        },
      ];
    }
  }

  // Simulated AI Chatbot Response Engine with Real Backend Memory DB Search Hook
  function handleSendMessage(text: string) {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Math.random().toString(),
      sender: "user",
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setIsTyping(true);

    const lower = text.toLowerCase();

    // Check if the user is asking to search backend memory logs
    const isSearchQuery = lower.includes("search") || lower.includes("find") || lower.includes("history") || lower.includes("what did i do") || lower.includes("what did i work on") || lower.includes("recent logs");
    
    if (isSearchQuery) {
      // Resolve search query term
      let queryTerm = "coding";
      if (lower.includes("database") || lower.includes("db") || lower.includes("sql") || lower.includes("postgres")) {
        queryTerm = "database";
      } else if (lower.includes("debug") || lower.includes("error") || lower.includes("crash") || lower.includes("fix")) {
        queryTerm = "debugging";
      } else if (lower.includes("react") || lower.includes("frontend") || lower.includes("css") || lower.includes("ui")) {
        queryTerm = "frontend";
      } else if (lower.includes("python") || lower.includes("django") || lower.includes("backend")) {
        queryTerm = "backend";
      } else {
        const match = text.match(/(?:search for|find|about)\s+(\w+)/i);
        if (match && match[1]) {
          queryTerm = match[1];
        }
      }

      // Query database search API
      apiCall(`/memories/search?q=${encodeURIComponent(queryTerm)}`)
        .then((data) => {
          const results = data.results || [];
          let responseText = "";

          if (results.length > 0) {
            const listText = results
              .slice(0, 3)
              .map((r: any, idx: number) => `${idx + 1}. **${r.content}** \n   *(Fit: ${Math.round(r.similarity * 100)}%, Importance: ${Math.round(r.importance_score * 100)}%)*`)
              .join("\n\n");
            
            responseText = `🔍 **I searched your DevMind vector database index for '${queryTerm}':**\n\nI located these matching memories from your real coding history:\n\n${listText}\n\n*Coach Recommendation*: Since we tracked these signals, we've updated your focus gaps. Try learning supplementary tools mapped in your Roadmaps tab!`;
          } else {
            responseText = `🔍 **I searched your DevMind vector database index for '${queryTerm}':**\n\nNo close memories found in the database. Make sure you are using your connected workspace tools so your sessions get parsed into database signals!`;
          }

          const coachMsg: Message = {
            id: Math.random().toString(),
            sender: "coach",
            text: responseText,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, coachMsg]);
          setIsTyping(false);
        })
        .catch((err) => {
          const coachMsg: Message = {
            id: Math.random().toString(),
            sender: "coach",
            text: `⚠️ I was unable to connect to the memories database: *${err.message}*. Ensure your backend server is active at ${API_URL}.`,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, coachMsg]);
          setIsTyping(false);
        });
      return;
    }

    // Default chat responses
    setTimeout(() => {
      let replyText = "";
      const topRec = recommendations[0]?.content || "focus on engineering gaps";
      const topSkill = profile?.skill_summary?.[0]?.skill_name || "Python";
      const activeMatch = careerMatches?.[0];

      if (lower.includes("hi") || lower.includes("hello") || lower.includes("hey") || lower.includes("who are you")) {
        replyText = `Hello! I'm your DevMind Coach. I specialize in looking at your real programming signals and guiding your learning roadmap. How can I help you? You can ask me to:
- **Search your coding history** (e.g. "search my logs for database")
- **Build a learning schedule** for any skill gap
- **Analyze your job matches**
- **Test your technical skills** for mock interviews`;
      } else if (lower.includes("skill") || lower.includes("profile") || lower.includes("proficiency") || lower.includes("know")) {
        const skillsList = profile?.skill_summary
          ? profile.skill_summary
              .slice(0, 5)
              .map((s) => `- **${s.skill_name}** (${Math.round(s.proficiency_score * 100)}% fit, ${s.signal_count} signals)`)
              .join("\n")
          : "- No skills tracked yet.";
        replyText = `📊 Here is your live skill summary compiled from your code commits and debug events:\n\n${skillsList}\n\nYour strongest area is **${topSkill}**. I recommend reviewing the **Recommendations** panel to see what complement skills will yield the best career growth.`;
      } else if (lower.includes("learn") || lower.includes("recommend") || lower.includes("gap") || lower.includes("next")) {
        const recList = recommendations.length > 0
          ? recommendations.map((r, i) => `${i + 1}. **${r.content}** (${Math.round(r.relevance_score * 100)}% relevance score)`).join("\n")
          : "No recommendation gaps identified yet. Try capturing a few more coding sessions!";
        replyText = `🎯 Here are the highest-confidence learning recommendations I've mapped for you:\n\n${recList}\n\nI suggest checking out our **Learning Roadmaps** below, which breaks these down into structured weekly study schedules.`;
      } else if (lower.includes("career") || lower.includes("job") || lower.includes("match") || lower.includes("fit") || lower.includes("company")) {
        if (activeMatch) {
          replyText = `💼 I've identified several strong career alignment matches. Your closest fit is **${activeMatch.title}** at **${activeMatch.company}** with a fit confidence of **${Math.round(activeMatch.fit_score * 100)}%**.\n\n*Coach Insights:* ${activeMatch.fit_reason}\n\nGo to the **Career Intelligence** tab on this page to view a full gap-map of missing skills needed to secure this exact role.`;
        } else {
          replyText = `💼 I couldn't load active job matches. Head to the **Career Matches** page in the main navigation menu to trigger the Apify job fetcher and see personalized roles!`;
        }
      } else if (lower.includes("interview") || lower.includes("question") || lower.includes("practice") || lower.includes("mock")) {
        replyText = `🚀 Ready to test your skills? Click on the **Interview Prep** tab at the top of the dashboard. You can select any job title, and I will ask you 3 interview questions with personalized scoring and ideal solutions.`;
      } else if (lower.includes("react") || lower.includes("next.js") || lower.includes("nextjs") || lower.includes("frontend")) {
        replyText = `🌐 **React & Frontend Engineering Guidance:**
- **Core Focus**: Master functional hooks (\`useEffect\`, \`useMemo\`, \`useCallback\`) and state lifecycles.
- **Architectures**: Understand Next.js App Router server vs client separation, hydration, and routing layouts.
- **Tools**: Get comfortable with Tailwind CSS, ESLint, and standard bundling concepts.
- **Tip**: Keep components highly granular and isolated to avoid massive re-renders.`;
      } else if (lower.includes("python") || lower.includes("django") || lower.includes("fastapi") || lower.includes("backend")) {
        replyText = `⚙️ **Python & Backend Engineering Guidance:**
- **Core Focus**: Async concurrency, generators, context managers, and type hinting.
- **API Design**: RESTful design principles, secure OAuth2 protocols, and input validation (using Pydantic).
- **Database Layer**: Optimize queries using SQLAlchemy/Django ORM, write migration files, and implement caching patterns.
- **Tip**: Write unit test suites with \`pytest\` mocking external API connections.`;
      } else if (lower.includes("docker") || lower.includes("deployment") || lower.includes("ci/cd")) {
        replyText = `🐳 **Docker & Devops Engineering Guidance:**
- **Core Focus**: Understand multi-stage builds (keeping images small), ports mapping, environment files, and container volumes.
- **Orchestration**: Write composite \`docker-compose.yml\` files that link server, cache, and database containers seamlessly.
- **Tip**: Never store production secrets directly inside image Dockerfiles; always pass them at runtime as env variables.`;
      } else {
        replyText = `💡 That is an interesting query! As your DevMind Coach, I recommend integrating **${topRec}** into your current workflow. Practice writing modular files, test-driven logic, and let your code history create developer signals.\n\nLet me know if you want me to expand on frontend best practices, backend deployment, or mock interview answers!`;
      }

      const coachMsg: Message = {
        id: Math.random().toString(),
        sender: "coach",
        text: replyText,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, coachMsg]);
      setIsTyping(false);
    }, 1000);
  }

  // Interview Simulator Handler
  function startMockInterview(job: CareerMatch) {
    setInterviewJob(job);
    setInterviewStep(0);
    setInterviewAnswers([]);
    setCurrentAnswer("");
    setFeedbackHistory([]);
    setIdealAnswersHistory([]);
  }

  function handleAnswerSubmit() {
    if (!currentAnswer.trim() || !interviewJob) return;

    const questions = getInterviewQuestions(interviewJob.title);
    const activeQuestion = questions[interviewStep];
    const userAns = currentAnswer.toLowerCase();

    // Grade answer based on keyword matches
    let matchCount = 0;
    const matchedWords: string[] = [];
    activeQuestion.idealKeywords.forEach((kw) => {
      if (userAns.includes(kw)) {
        matchCount++;
        matchedWords.push(kw);
      }
    });

    const scorePct = Math.round((matchCount / activeQuestion.idealKeywords.length) * 100);
    let gradeLabel = "Needs Work";
    let gradeColor = "text-[#FF6B6B]";
    let feedback = "";

    if (scorePct >= 80) {
      gradeLabel = "Excellent Answer!";
      gradeColor = "text-[#4CFF82]";
      feedback = "You gave a highly accurate technical answer, identifying all core architectural points.";
    } else if (scorePct >= 40) {
      gradeLabel = "Solid Answer";
      gradeColor = "text-[#FFAE4C]";
      feedback = `Good description. You correctly mentioned ${matchedWords.join(", ")}. However, you would improve by also addressing: ${activeQuestion.idealKeywords.filter(k => !matchedWords.includes(k)).join(", ")}.`;
    } else {
      feedback = `You missed the primary concepts for this topic. Be sure to reference ${activeQuestion.idealKeywords.join(", ")} when explaining this.`;
    }

    const review = `🎯 **Grade: ${gradeLabel} (${scorePct}%)**\n\n${feedback}`;

    setInterviewAnswers((prev) => [...prev, currentAnswer]);
    setFeedbackHistory((prev) => [...prev, review]);
    setIdealAnswersHistory((prev) => [...prev, activeQuestion.sampleAnswer]);
    setCurrentAnswer("");
    setInterviewStep((prev) => prev + 1);
  }

  function resetInterview() {
    setInterviewJob(null);
    setInterviewStep(-1);
    setInterviewAnswers([]);
    setCurrentAnswer("");
    setFeedbackHistory([]);
    setIdealAnswersHistory([]);
  }

  // Selected job for Skill Alignment
  const selectedJob = careerMatches.find((m) => m.id === selectedJobId) || careerMatches[0];

  return (
    <main className="min-h-screen bg-[#0A0E14] text-[#E8EAED] px-6 py-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Banner Section */}
        <header className="mb-8 bg-gradient-to-r from-[#111827] via-[#1E293B] to-[#111827] border border-[#1C2333] rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(circle_at_top_right,rgba(76,141,255,0.15),transparent)] pointer-events-none"></div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="bg-[#4C8DFF]/20 text-[#4C8DFF] text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded border border-[#4C8DFF]/30 tracking-wider">
                  AI Platform
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#4CFF82] animate-ping"></span>
                <span className="text-[11px] text-[#8A9099] font-mono">Coach Synchronized</span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-[#FFFFFF] to-[#A0AEC0]">
                AI Mentor & Career Intelligence
              </h1>
              <p className="text-sm text-[#8A9099] mt-1 max-w-2xl">
                Personalized learning pathways, diagnostic code evaluation, and automated job gap-mapping synced from your developer workspace.
              </p>
            </div>
            
            {/* Simple Study Streak Widget */}
            <div className="flex items-center gap-3 bg-[#0A0E14]/60 border border-[#1C2333] rounded-xl px-4 py-3 shrink-0">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center text-amber-400 font-bold border border-amber-500/30">
                🔥
              </div>
              <div>
                <p className="text-[11px] text-[#8A9099] font-mono uppercase tracking-wider">Learning Streak</p>
                <p className="text-sm font-semibold">{studyStreak} Days Active</p>
              </div>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="flex border-b border-[#1C2333] mb-8 gap-2">
          <button
            onClick={() => setActiveTab("coach")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all ${
              activeTab === "coach"
                ? "border-[#4C8DFF] text-[#4C8DFF]"
                : "border-transparent text-[#8A9099] hover:text-[#E8EAED]"
            }`}
          >
            <span>🎯</span> AI Learning Coach
          </button>
          <button
            onClick={() => setActiveTab("career")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all ${
              activeTab === "career"
                ? "border-[#4C8DFF] text-[#4C8DFF]"
                : "border-transparent text-[#8A9099] hover:text-[#E8EAED]"
            }`}
          >
            <span>📊</span> Career Intelligence Hub
          </button>
          <button
            onClick={() => setActiveTab("interview")}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all ${
              activeTab === "interview"
                ? "border-[#4C8DFF] text-[#4C8DFF]"
                : "border-transparent text-[#8A9099] hover:text-[#E8EAED]"
            }`}
          >
            <span>📝</span> Interview Prep Simulation
          </button>
        </div>

        {/* Tab Content 1: AI Learning Coach */}
        {activeTab === "coach" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Left side: Recommendations & Captured Highlights */}
            <div className="lg:col-span-5 space-y-6">
              
              {/* Captured Highlights from backend Profile */}
              {profile?.activity_summary?.recent_highlights && (
                <div className="bg-[#111622] border border-[#1C2333] rounded-xl p-5 relative overflow-hidden">
                  <h3 className="font-semibold text-sm text-[#4C8DFF] uppercase font-mono tracking-wider mb-3 flex items-center gap-1.5">
                    <span>📡</span> Captured Backend Signals
                  </h3>
                  <div className="space-y-2">
                    {profile.activity_summary.recent_highlights.slice(0, 3).map((hl, idx) => (
                      <div key={idx} className="border border-[#1C2333] rounded-lg p-3 text-xs bg-[#0A0E14] text-[#8A9099] leading-relaxed">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] text-[#4C8DFF] font-mono">Signal #{idx+1}</span>
                          <span className="text-[10px] bg-[#1C2333] text-[#8A9099] px-1 py-0.5 rounded font-mono">
                            Imp: {Math.round(hl.importance_score * 100)}%
                          </span>
                        </div>
                        <p className="text-[#E8EAED]">{hl.content}</p>
                      </div>
                    ))}
                    {profile.activity_summary.recent_highlights.length === 0 && (
                      <p className="text-xs text-[#8A9099]">No session highlights registered in database yet.</p>
                    )}
                  </div>
                </div>
              )}

              {/* Goal Widget */}
              <div className="bg-[#111622] border border-[#1C2333] rounded-xl p-5 relative overflow-hidden">
                <h3 className="font-semibold text-sm text-[#4C8DFF] uppercase font-mono tracking-wider mb-2">Weekly Milestones</h3>
                <div className="flex items-center gap-2 mb-3">
                  <input
                    type="text"
                    value={weeklyGoal}
                    onChange={(e) => setWeeklyGoal(e.target.value)}
                    className="bg-transparent border-b border-[#2C354D] text-sm text-[#E8EAED] focus:border-[#4C8DFF] focus:outline-none flex-1 py-1"
                  />
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => {
                      if (weeklyGoal.trim()) {
                        setCompletedGoals(prev => [...prev, weeklyGoal]);
                        setWeeklyGoal("");
                        setStudyStreak(s => s + 1);
                      }
                    }}
                    className="text-xs bg-[#4C8DFF]/15 text-[#4C8DFF] hover:bg-[#4C8DFF]/25 border border-[#4C8DFF]/30 px-3 py-1.5 rounded transition-all"
                  >
                    ✓ Complete Goal
                  </button>
                </div>
                
                {completedGoals.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[#1C2333]">
                    <p className="text-[11px] text-[#8A9099] font-mono mb-2">COMPLETED WEEKS</p>
                    <div className="space-y-1">
                      {completedGoals.map((g, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-[#8A9099] line-through decoration-[#4C8DFF]">
                          <span>🏆</span> {g}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Recommendations Spotlight */}
              <div>
                <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
                  <span>🎯</span> Personalized Focus Gaps
                </h2>
                
                {recommendations.length === 0 ? (
                  <div className="bg-[#111622] border border-[#1C2333] rounded-xl p-6 text-center text-[#8A9099] text-sm">
                    No recommendations found. Try syncing more commits on your Profile page.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recommendations.map((rec, idx) => {
                      const isTop = idx === 0;
                      return (
                        <div
                          key={idx}
                          className={`border rounded-xl p-4 transition-all ${
                            isTop
                              ? "bg-gradient-to-br from-[#111622] to-[#18233C] border-[#4C8DFF]/50 shadow-[0_4px_20px_-8px_rgba(76,141,255,0.2)]"
                              : "bg-[#111622] border-[#1C2333] hover:border-[#2C354D]"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2 mb-2">
                            <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold uppercase ${
                              isTop 
                                ? "bg-[#4C8DFF]/20 text-[#4C8DFF] border border-[#4C8DFF]/30" 
                                : "bg-[#1C2333] text-[#8A9099] border border-[#2C354D]"
                            }`}>
                              {isTop ? "Highest Priority Gap" : "Secondary Skill Gap"}
                            </span>
                            <span className="text-xs font-mono text-[#4C8DFF]">
                              {Math.round(rec.relevance_score * 100)}% Match Gap
                            </span>
                          </div>
                          
                          <p className="font-mono text-sm text-[#E8EAED] font-semibold mb-3">{rec.content}</p>
                          
                          {/* Accordion Roadmap Trigger */}
                          <div className="flex items-center justify-between border-t border-[#1C2333]/60 pt-3">
                            <button
                              onClick={() => setExpandedRoadmap(expandedRoadmap === idx ? null : idx)}
                              className="text-xs text-[#8A9099] hover:text-[#E8EAED] flex items-center gap-1 transition-all"
                            >
                              <span>{expandedRoadmap === idx ? "▼ Hide" : "▶ Show"}</span> Learning Roadmap
                            </button>
                            
                            <button
                              onClick={() => {
                                handleSendMessage(`Give me learning resources and project ideas for: ${rec.content}`);
                              }}
                              className="text-xs text-[#4C8DFF] hover:underline"
                            >
                              Ask Coach →
                            </button>
                          </div>

                          {/* Roadmap Detail Steps */}
                          {expandedRoadmap === idx && (
                            <div className="mt-4 pt-3 border-t border-[#1C2333] space-y-3 pl-2">
                              {getRoadmapSteps(rec.content).map((step, sidx) => (
                                <div key={sidx} className="relative pl-4 border-l border-[#2C354D] last:border-0 pb-1">
                                  <div className="absolute left-[-5px] top-1.5 w-2.5 h-2.5 rounded-full bg-[#4C8DFF]"></div>
                                  <h4 className="text-xs font-semibold text-[#E8EAED] font-mono">{step.week}</h4>
                                  <p className="text-[11px] text-[#8A9099] mt-0.5 leading-relaxed">{step.desc}</p>
                                  <div className="flex gap-1.5 mt-1 flex-wrap">
                                    {step.resources.map((resName, rIdx) => (
                                      <span key={rIdx} className="text-[9px] bg-[#1C2333] text-[#8A9099] px-1.5 py-0.5 rounded border border-[#2C354D]">
                                        📚 {resName}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

            </div>

            {/* Right side: Interactive Coach Chat */}
            <div className="lg:col-span-7 flex flex-col h-[600px] bg-[#111622] border border-[#1C2333] rounded-2xl overflow-hidden shadow-xl">
              
              {/* Chat Header */}
              <div className="bg-[#181F30] border-b border-[#1C2333] p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#4C8DFF] to-[#804CFF] flex items-center justify-center text-white text-lg font-bold">
                    🤖
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">AI Technical Coach</h3>
                    <p className="text-xs text-[#4CFF82] flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#4CFF82]"></span> Connected to Vector Index
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (profile) {
                      const name = profile?.skill_summary?.[0]?.skill_name || "Python";
                      setMessages([
                        {
                          id: "greeting",
                          sender: "coach",
                          text: `👋 Chat history cleared. Ask me anything about your skill path! (Strongest area: **${name}**).`,
                          timestamp: new Date(),
                        },
                      ]);
                    }
                  }}
                  className="text-xs text-[#8A9099] hover:text-[#E8EAED] border border-[#2C354D] hover:bg-[#1C2333] px-2 py-1 rounded transition-all"
                >
                  Clear History
                </button>
              </div>

              {/* Chat Messages Panel */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans scrollbar-thin scrollbar-thumb-gray-800">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed border ${
                        msg.sender === "user"
                          ? "bg-[#4C8DFF]/15 text-[#E8EAED] border-[#4C8DFF]/30 rounded-tr-none font-medium"
                          : "bg-[#181F30] text-[#E8EAED] border-[#2C354D] rounded-tl-none"
                      }`}
                    >
                      {/* Simple custom markdown renderer helper for bold text and bullet lines */}
                      <div className="space-y-1.5 whitespace-pre-line">
                        {msg.text.split("\n").map((line, lIdx) => {
                          let content: React.ReactNode = line;
                          
                          // Check if bullet line
                          const isBullet = line.trim().startsWith("- ");
                          let displayLine = line;
                          if (isBullet) {
                            displayLine = line.trim().substring(2);
                          }

                          // Simple bold parser: **word** -> <strong>word</strong>
                          const parts = displayLine.split(/\*\*([^*]+)\*\*/g);
                          if (parts.length > 1) {
                            content = (
                              <>
                                {parts.map((part, pIdx) =>
                                  pIdx % 2 === 1 ? <strong key={pIdx} className="text-[#4C8DFF] font-semibold">{part}</strong> : part
                                )}
                              </>
                            );
                          }

                          return (
                            <p key={lIdx} className={isBullet ? "pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-[#4C8DFF]" : ""}>
                              {content}
                            </p>
                          );
                        })}
                      </div>
                      <span className="block text-[10px] text-[#8A9099] text-right mt-2 font-mono">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-[#181F30] border border-[#2C354D] rounded-2xl rounded-tl-none p-4 flex gap-1.5 items-center">
                      <div className="w-2 h-2 rounded-full bg-[#4C8DFF] animate-bounce"></div>
                      <div className="w-2 h-2 rounded-full bg-[#4C8DFF] animate-bounce delay-100"></div>
                      <div className="w-2 h-2 rounded-full bg-[#4C8DFF] animate-bounce delay-200"></div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Prompts Suggestions - Hooked to Vector Index Search */}
              <div className="px-4 py-2 border-t border-[#1C2333]/50 flex gap-2 overflow-x-auto bg-[#0E1320] no-scrollbar">
                {[
                  "Search logs for database",
                  "What did I work on recently?",
                  "Show my debugging history",
                  "How do I improve my skills?",
                ].map((sug, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(sug)}
                    className="text-xs text-[#8A9099] hover:text-[#4C8DFF] border border-[#2C354D] hover:border-[#4C8DFF]/40 rounded-full px-3 py-1 bg-[#111622] whitespace-nowrap transition-all"
                  >
                    🔍 {sug}
                  </button>
                ))}
              </div>

              {/* Chat Input Bar */}
              <div className="p-4 border-t border-[#1C2333] bg-[#181F30]">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage(inputText);
                  }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Search logs for a technology or ask for learning paths..."
                    className="flex-1 bg-[#0A0E14] border border-[#2C354D] hover:border-[#4C8DFF]/30 focus:border-[#4C8DFF] focus:outline-none rounded-xl px-4 py-2.5 text-sm text-[#E8EAED] transition-all"
                  />
                  <button
                    type="submit"
                    className="bg-[#4C8DFF] hover:bg-[#3572DF] text-white rounded-xl px-5 py-2.5 text-sm font-semibold transition-all shadow-md flex items-center gap-1.5"
                  >
                    Send ➔
                  </button>
                </form>
              </div>

            </div>

          </div>
        )}

        {/* Tab Content 2: Career Intelligence Hub */}
        {activeTab === "career" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* Left Column: Job matches grid */}
              <div className="lg:col-span-5 space-y-4">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <span>💼</span> Matching Career Options
                </h2>
                
                {careerMatches.length === 0 ? (
                  <div className="bg-[#111622] border border-[#1C2333] rounded-xl p-6 text-center text-[#8A9099] text-sm">
                    No active job matches. Try fetching LinkedIn postings first!
                  </div>
                ) : (
                  <div className="space-y-3">
                    {careerMatches.map((job) => {
                      const isSelected = selectedJobId === job.id;
                      return (
                        <div
                          key={job.id}
                          onClick={() => setSelectedJobId(job.id)}
                          className={`p-4 border rounded-xl cursor-pointer transition-all ${
                            isSelected
                              ? "bg-gradient-to-br from-[#18233C] to-[#111622] border-[#4C8DFF]"
                              : "bg-[#111622] border-[#1C2333] hover:border-[#2C354D]"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#1C2333] border border-[#2C354D] text-[#8A9099]">
                              {job.company}
                            </span>
                            <span className="text-sm font-mono font-bold text-[#4CFF82]">
                              {Math.round(job.fit_score * 100)}% Match Fit
                            </span>
                          </div>
                          
                          <h4 className="font-semibold text-[#E8EAED] text-sm">{job.title}</h4>
                          <p className="text-xs text-[#8A9099] mt-1">📍 {job.location}</p>
                          
                          <div className="mt-3 flex justify-between items-center text-xs">
                            <a
                              href={job.url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-[#4C8DFF] hover:underline"
                            >
                              View Posting ↗
                            </a>
                            <span className="text-xs text-[#8A9099]">Click to analyze gaps</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Right Column: Skill Alignment Gap Map */}
              <div className="lg:col-span-7 bg-[#111622] border border-[#1C2333] rounded-2xl p-6">
                {selectedJob ? (
                  <div>
                    {/* Header */}
                    <div className="border-b border-[#1C2333] pb-4 mb-6">
                      <div className="flex justify-between items-start gap-4">
                        <div>
                          <p className="text-xs text-[#4C8DFF] font-mono uppercase font-semibold">Match Gap Analysis</p>
                          <h3 className="text-xl font-bold mt-1">{selectedJob.title}</h3>
                          <p className="text-sm text-[#8A9099] mt-0.5">{selectedJob.company} — {selectedJob.location}</p>
                        </div>
                        <button
                          onClick={() => startMockInterview(selectedJob)}
                          className="bg-[#4C8DFF]/15 text-[#4C8DFF] hover:bg-[#4C8DFF]/25 border border-[#4C8DFF]/30 text-xs px-3.5 py-2 rounded-xl transition-all font-semibold font-mono"
                        >
                          Start Interview Prep ➜
                        </button>
                      </div>
                    </div>

                    {/* Fit Reason */}
                    <div className="bg-[#181F30] border border-[#2C354D] rounded-xl p-4 mb-6">
                      <h4 className="text-xs font-semibold uppercase text-[#8A9099] font-mono mb-2">Mentor Fit Overview</h4>
                      <p className="text-sm text-[#E8EAED] leading-relaxed italic">
                        "{selectedJob.fit_reason}"
                      </p>
                    </div>

                    {/* Skill Alignment Map (Dynamic) */}
                    <div>
                      <h4 className="text-xs font-semibold uppercase text-[#8A9099] font-mono mb-3">Workspace Skill Alignment Mapping</h4>
                      
                      <div className="space-y-4">
                        {/* Acquired Skills */}
                        <div>
                          <div className="flex items-center gap-2 mb-2 text-xs text-[#4CFF82] font-mono font-semibold">
                            <span>✓</span> ACQUIRED COMPETENCIES (TRACKED ON DEVMINDS)
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            {profile?.skill_summary && profile.skill_summary.length > 0 ? (
                              profile.skill_summary.slice(0, 5).map((s, i) => (
                                <div key={i} className="flex items-center gap-1.5 bg-[#0F2D1F] border border-[#166534] text-[#4CFF82] px-2.5 py-1 rounded-lg text-xs font-mono">
                                  <span>●</span> {s.skill_name}
                                </div>
                              ))
                            ) : (
                              <span className="text-xs text-[#8A9099]">No acquired competencies found.</span>
                            )}
                          </div>
                        </div>

                        {/* Missing Skills */}
                        <div className="pt-2">
                          <div className="flex items-center gap-2 mb-2 text-xs text-[#FFAE4C] font-mono font-semibold">
                            <span>⚠</span> PRIMARY GAP GAPS (RECOMMENDED TO ACQUIRE)
                          </div>
                          
                          <div className="space-y-2">
                            {recommendations.slice(0, 3).map((rec, i) => {
                              const tech = rec.content.split(" ").slice(-1)[0] || rec.content;
                              return (
                                <div key={i} className="flex justify-between items-center bg-[#251A0D] border border-[#7C2D12]/60 text-[#FFAE4C] p-3 rounded-lg text-xs">
                                  <div className="flex items-center gap-2">
                                    <span>○</span>
                                    <span className="font-mono font-semibold">{tech}</span>
                                  </div>
                                  <button
                                    onClick={() => {
                                      setWeeklyGoal(`Complete introductory project in ${tech}`);
                                      alert(`Goal created: "Complete introductory project in ${tech}". Check the 'AI Learning Coach' tab weekly goals!`);
                                    }}
                                    className="text-[10px] bg-[#FFAE4C]/20 border border-[#FFAE4C]/30 text-[#FFAE4C] px-2 py-0.5 rounded hover:bg-[#FFAE4C]/35 transition-all font-semibold font-mono"
                                  >
                                    + Add Learning Goal
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>

                    </div>

                  </div>
                ) : (
                  <div className="text-center text-[#8A9099] py-12">
                    Please select a job match on the left panel to display analysis.
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* Tab Content 3: Interview Prep Simulator */}
        {activeTab === "interview" && (
          <div className="bg-[#111622] border border-[#1C2333] rounded-2xl p-6 max-w-4xl mx-auto">
            
            {interviewStep === -1 ? (
              <div className="text-center py-10 space-y-6">
                <div className="w-16 h-16 bg-[#4C8DFF]/15 text-[#4C8DFF] rounded-2xl flex items-center justify-center text-3xl mx-auto border border-[#4C8DFF]/30">
                  🎙
                </div>
                
                <div>
                  <h3 className="text-lg font-bold">AI Technical Mock Interview Simulator</h3>
                  <p className="text-sm text-[#8A9099] max-w-lg mx-auto mt-1">
                    Select one of your matched positions. The AI Mentor will ask you 3 customized questions regarding code quality, system layout, or database operations, grading you on conceptual alignment.
                  </p>
                </div>

                <div className="max-w-md mx-auto space-y-2">
                  <p className="text-xs text-[#8A9099] font-mono uppercase tracking-wider mb-2">SELECT A ROLE TO PREPARE FOR</p>
                  {careerMatches.map((job) => (
                    <button
                      key={job.id}
                      onClick={() => startMockInterview(job)}
                      className="w-full bg-[#181F30] hover:bg-[#20293D] border border-[#2C354D] hover:border-[#4C8DFF]/50 text-left p-3.5 rounded-xl transition-all flex justify-between items-center text-xs"
                    >
                      <div>
                        <span className="font-semibold text-[#E8EAED]">{job.title}</span>
                        <span className="text-[#8A9099] block text-[11px] mt-0.5">{job.company}</span>
                      </div>
                      <span className="text-[#4C8DFF] font-mono">Select ➜</span>
                    </button>
                  ))}
                  
                  {careerMatches.length === 0 && (
                    <div className="text-xs text-[#8A9099]">
                      No active jobs loaded. Let's create a generic interview simulator!
                    </div>
                  )}
                  
                  <button
                    onClick={() => {
                      const mockJob = {
                        id: "generic",
                        title: "Fullstack Software Developer",
                        company: "DevMind Engineering",
                        location: "Remote",
                        url: "",
                        fit_score: 0.8,
                        fit_reason: "Generic practice template",
                      };
                      startMockInterview(mockJob);
                    }}
                    className="w-full border border-dashed border-[#2C354D] hover:border-[#4C8DFF] text-[#8A9099] hover:text-[#4C8DFF] p-3 text-xs rounded-xl transition-all text-center"
                  >
                    🛠 Practice Generic Fullstack Role
                  </button>
                </div>
              </div>
            ) : (
              <div>
                {/* Interview Header */}
                <div className="flex items-center justify-between border-b border-[#1C2333] pb-4 mb-6">
                  <div>
                    <span className="text-[10px] text-[#4C8DFF] font-mono uppercase font-semibold">Active Interviewing Room</span>
                    <h3 className="font-bold text-base mt-0.5">{interviewJob?.title}</h3>
                    <p className="text-xs text-[#8A9099]">{interviewJob?.company}</p>
                  </div>
                  
                  <button
                    onClick={resetInterview}
                    className="text-xs text-[#8A9099] hover:text-[#FF6B6B] border border-[#2C354D] hover:border-[#FF6B6B]/40 px-3 py-1.5 rounded transition-all"
                  >
                    Quit Session
                  </button>
                </div>

                {/* Progress Indicators */}
                <div className="flex gap-2 mb-6">
                  {[0, 1, 2].map((stepIdx) => (
                    <div
                      key={stepIdx}
                      className={`flex-1 h-1.5 rounded-full transition-all ${
                        interviewStep > stepIdx
                          ? "bg-[#4C8DFF]"
                          : interviewStep === stepIdx
                          ? "bg-[#4C8DFF]/40 animate-pulse"
                          : "bg-[#1C2333]"
                      }`}
                    ></div>
                  ))}
                </div>

                {/* Main Q&A Flow */}
                {interviewStep < 3 ? (
                  <div className="space-y-6">
                    {/* The Question */}
                    <div className="bg-[#181F30] border border-[#2C354D] rounded-xl p-5">
                      <p className="text-[10px] text-[#4C8DFF] font-mono font-semibold uppercase tracking-wider mb-2">
                        Question {interviewStep + 1} of 3
                      </p>
                      <p className="text-sm font-semibold text-[#E8EAED] leading-relaxed">
                        {getInterviewQuestions(interviewJob?.title || "")[interviewStep].question}
                      </p>
                    </div>

                    {/* Developer Response Area */}
                    <div className="space-y-2">
                      <label className="text-xs text-[#8A9099] font-mono uppercase">Your Response</label>
                      <textarea
                        value={currentAnswer}
                        onChange={(e) => setCurrentAnswer(e.target.value)}
                        placeholder="Type your explanation here. Be sure to reference primary mechanisms, tradeoffs, and code terms..."
                        rows={6}
                        className="w-full bg-[#0A0E14] border border-[#2C354D] focus:border-[#4C8DFF] focus:outline-none rounded-xl p-4 text-sm text-[#E8EAED] transition-all font-sans leading-relaxed"
                      />
                    </div>

                    {/* Submission button */}
                    <div className="flex justify-end gap-3 pt-2">
                      <button
                        onClick={() => {
                          const question = getInterviewQuestions(interviewJob?.title || "")[interviewStep];
                          setCurrentAnswer(question.sampleAnswer);
                        }}
                        className="text-xs border border-[#2C354D] text-[#8A9099] hover:text-[#E8EAED] hover:bg-[#1C2333] px-3.5 py-2 rounded-xl transition-all"
                      >
                        Help (Paste Sample Response)
                      </button>
                      <button
                        onClick={handleAnswerSubmit}
                        disabled={!currentAnswer.trim()}
                        className="bg-[#4C8DFF] hover:bg-[#3572DF] disabled:bg-[#1C2333] disabled:text-[#8A9099] text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition-all"
                      >
                        Submit Response ➔
                      </button>
                    </div>
                  </div>
                ) : (
                  // Interview Completed & Feedback Report
                  <div className="space-y-6">
                    <div className="text-center py-6">
                      <div className="w-12 h-12 bg-[#4CFF82]/15 text-[#4CFF82] rounded-full flex items-center justify-center text-xl mx-auto border border-[#4CFF82]/30 mb-3 animate-bounce">
                        ✓
                      </div>
                      <h4 className="font-bold text-lg">Interview Simulation Complete!</h4>
                      <p className="text-xs text-[#8A9099] mt-0.5">Let's review the evaluation and key lessons from your answers.</p>
                    </div>

                    {/* History review list */}
                    <div className="space-y-6">
                      {getInterviewQuestions(interviewJob?.title || "").map((q, idx) => (
                        <div key={idx} className="border border-[#1C2333] rounded-xl p-5 space-y-4 bg-[#141A28]">
                          <div>
                            <span className="text-[10px] text-[#4C8DFF] font-mono font-semibold uppercase">Question {idx + 1}</span>
                            <h5 className="font-bold text-xs text-[#E8EAED] mt-0.5 leading-relaxed">{q.question}</h5>
                          </div>

                          <div className="bg-[#0A0E14] border border-[#1C2333] rounded-lg p-3.5 text-xs text-[#8A9099]">
                            <span className="text-[10px] text-[#8A9099] font-mono uppercase block mb-1">Your Submission:</span>
                            <p className="italic">"{interviewAnswers[idx] || "No answer submitted."}"</p>
                          </div>

                          {/* Feedback evaluation */}
                          <div className="bg-[#181F30] border border-[#2C354D] rounded-lg p-4 text-xs">
                            <span className="text-[10px] text-[#4C8DFF] font-mono uppercase block mb-2">Coach Evaluation:</span>
                            <div className="space-y-2 whitespace-pre-line text-[#E8EAED] leading-relaxed">
                              {feedbackHistory[idx]?.split("\n").map((line, lIdx) => {
                                let content: React.ReactNode = line;
                                const isBold = line.includes("**");
                                if (isBold) {
                                  const parts = line.split(/\*\*([^*]+)\*\*/g);
                                  content = (
                                    <>
                                      {parts.map((p, pIdx) => pIdx % 2 === 1 ? <strong key={pIdx} className="text-[#4CFF82]">{p}</strong> : p)}
                                    </>
                                  );
                                }
                                return <p key={lIdx}>{content}</p>;
                              })}
                            </div>
                          </div>

                          {/* Ideal answer */}
                          <div className="border border-dashed border-[#2C354D] rounded-lg p-4 text-xs text-[#8A9099] leading-relaxed">
                            <span className="text-[10px] text-[#8A9099] font-mono uppercase block mb-1">Sample Model Answer:</span>
                            <p>{idealAnswersHistory[idx]}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-center pt-4">
                      <button
                        onClick={resetInterview}
                        className="bg-[#4C8DFF] hover:bg-[#3572DF] text-white font-semibold text-xs px-6 py-2.5 rounded-xl transition-all"
                      >
                        Return & Practice Again
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>
        )}

      </div>
    </main>
  );
}