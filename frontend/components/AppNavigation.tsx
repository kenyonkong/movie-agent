"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Recommendations" },
  { href: "/movies", label: "Browse Movies" },
  { href: "/reviews", label: "My Reviews" },
  { href: "/taste-profile", label: "Taste Profile" },
];

export function AppNavigation() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[#BDB76B]/45 bg-[#FDFBD4]/90 shadow-[0_8px_30px_rgba(91,72,30,0.08)] backdrop-blur-xl">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center justify-items-center gap-4 px-4 py-3 md:grid-cols-[1fr_auto_1fr]">
        <Link
          href="/"
          className="group flex items-center gap-3 text-lg font-bold tracking-tight text-[#352D22] transition hover:text-[#8A5B2B] md:justify-self-start"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full border border-[#D4AF37] bg-[#FFFDF0] font-display text-sm text-[#826714] shadow-sm transition group-hover:bg-[#D4AF37]/20">
            MA
          </span>
          <span className="font-display">Movie Agent</span>
        </Link>

        <nav
          aria-label="Primary navigation"
          className="flex max-w-full gap-1 overflow-x-auto rounded-full border border-[#BDB76B]/70 bg-[#FFFDF0]/90 p-1.5 shadow-[0_8px_24px_rgba(91,72,30,0.10)]"
        >
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition ${
                  isActive
                    ? "bg-[#CE8946] text-[#2F251A] shadow-sm"
                    : "text-[#625845] hover:bg-[#BDB76B]/20 hover:text-[#352D22]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div aria-hidden="true" className="hidden md:block" />
      </div>
    </header>
  );
}
