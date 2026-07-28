"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Profile" },
  { href: "/career", label: "Career matches" },
  { href: "/resumes", label: "Resumes" },
  { href: "/skills", label: "Skills" },
  { href: "/reports", label: "Reports" },
  {href: "/coach", label:"Coach"}
];

export default function Nav(){
    const pathname = usePathname();
  return (
    <nav className="border-b border-[#1C2128] px-8 py-4 flex gap-6">
      {links.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className={`text-sm font-medium ${
            pathname === l.href ? "text-[#4C8DFF]" : "text-[#8A9099] hover:text-[#E8EAED]"
          }`}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}