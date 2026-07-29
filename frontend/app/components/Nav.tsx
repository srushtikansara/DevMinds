"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Profile" },
  { href: "/career", label: "Career" },
  { href: "/resumes", label: "Resumes" },
  { href: "/skills", label: "Skills" },
  { href: "/reports", label: "Reports" },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md bg-[#0A0E14]/80 border-b border-[#1C2128]">
      <div className="max-w-5xl mx-auto px-8 flex items-center justify-between h-14">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#4C8DFF]" />
          <span className="font-mono text-sm font-medium tracking-tight">DevMind</span>
        </div>
        <div className="flex gap-1">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  active
                    ? "bg-[#1C2128] text-[#E8EAED]"
                    : "text-[#8A9099] hover:text-[#E8EAED] hover:bg-[#1C2128]/50"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}