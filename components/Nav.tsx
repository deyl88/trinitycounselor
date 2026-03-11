"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const tabs = [
  {
    href: "/chat",
    label: "My Space",
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" className={clsx("w-6 h-6", active ? "fill-sand-700" : "fill-stone-400")} xmlns="http://www.w3.org/2000/svg">
        <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
      </svg>
    ),
  },
  {
    href: "/us",
    label: "Our Space",
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" className={clsx("w-6 h-6", active ? "fill-sand-700" : "fill-stone-400")} xmlns="http://www.w3.org/2000/svg">
        <path d="M16.5 12c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zm-9 0c1.66 0 3-1.34 3-3S9.16 6 7.5 6s-3 1.34-3 3 1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V20h14v-2.5c0-2.33-4.67-3.5-7-3.5zm9 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V20H24v-2.5c0-2.33-4.67-3.5-7.5-3.5z"/>
      </svg>
    ),
  },
  {
    href: "/couple",
    label: "Connect",
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" className={clsx("w-6 h-6", active ? "fill-sand-700" : "fill-stone-400")} xmlns="http://www.w3.org/2000/svg">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
      </svg>
    ),
  },
];

export default function Nav() {
  const path = usePathname();

  return (
    <nav className="border-t border-sand-100 bg-sand-50/80 backdrop-blur-sm pb-safe">
      <div className="flex">
        {tabs.map((tab) => {
          const active = path.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className="flex-1 flex flex-col items-center gap-1 py-3 transition active:scale-95"
            >
              {tab.icon(active)}
              <span className={clsx("text-xs font-medium", active ? "text-sand-700" : "text-stone-400")}>
                {tab.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
