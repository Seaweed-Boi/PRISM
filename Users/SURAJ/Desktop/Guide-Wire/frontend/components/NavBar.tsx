"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/worker", label: "Worker" },
  { href: "/admin", label: "Admin" },
  { href: "/fraud", label: "Fraud Engine" },
];

export default function NavBar() {
  const path = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[rgba(4,10,23,0.85)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative h-8 w-8 rounded-lg bg-gradient-to-br from-[#5cc8a1] to-[#4891f7] flex items-center justify-center text-white font-bold text-sm">
            P
            <span className="absolute inset-0 rounded-lg bg-gradient-to-br from-[#5cc8a1] to-[#4891f7] opacity-0 group-hover:opacity-60 blur-md transition-opacity" />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">
            PRISM
          </span>
          <span className="hidden sm:inline mono text-[10px] uppercase tracking-widest text-[#5cc8a1] opacity-70 ml-1">
            v1.0
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={[
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                path === l.href
                  ? "bg-[rgba(92,200,161,0.15)] text-[#5cc8a1] border border-[rgba(92,200,161,0.3)]"
                  : "text-[rgba(232,240,254,0.6)] hover:text-white hover:bg-white/5",
              ].join(" ")}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Status pill */}
        <div className="hidden md:flex items-center gap-2 mono text-xs text-[rgba(232,240,254,0.4)]">
          <span className="inline-block h-2 w-2 rounded-full bg-[#5cc8a1] animate-pulse" />
          System Online
        </div>
      </div>
    </nav>
  );
}
