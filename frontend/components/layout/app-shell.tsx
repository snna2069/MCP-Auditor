"use client";

import {
  ClipboardListIcon,
  LayoutDashboardIcon,
  PlusIcon,
  ServerIcon,
  ShieldIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { PointerEvent, ReactNode } from "react";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboardIcon },
  { href: "/servers", label: "Server Registry", icon: ServerIcon },
  { href: "/servers/new", label: "New Server", icon: PlusIcon },
  { href: "/audits", label: "Audit History", icon: ClipboardListIcon },
];

function NavLink({
  href,
  label,
  icon: Icon,
  isActive,
}: {
  href: string;
  label: string;
  icon: typeof ServerIcon;
  isActive: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Icon className="size-4 shrink-0" />
      {label}
    </Link>
  );
}

/** Picks the single most specific nav item matching the current path, so
 * sibling routes (e.g. "/servers" and "/servers/new") never both light up. */
function useActiveHref(pathname: string): string {
  let bestMatch = "";
  for (const item of NAV_ITEMS) {
    const matches =
      item.href === "/"
        ? pathname === "/"
        : pathname === item.href || pathname.startsWith(`${item.href}/`);
    if (matches && item.href.length > bestMatch.length) {
      bestMatch = item.href;
    }
  }
  return bestMatch;
}

function AppAtmosphere() {
  return (
    <div aria-hidden="true" className="app-atmosphere">
      <div className="app-atmosphere-grid" />
      <svg className="app-doodle app-doodle-top" viewBox="0 0 170 130" fill="none">
        <path d="M18 86c18-26 33-35 52-27 18 8 26 29 43 27 14-2 24-15 39-42" />
        <path d="M117 31l35 13-14 31" />
        <circle cx="31" cy="38" r="9" />
      </svg>
      <svg className="app-doodle app-doodle-bottom" viewBox="0 0 180 130" fill="none">
        <path d="M12 99c21-25 38-31 56-18 17 12 30 11 43-7 10-14 24-20 57-15" />
        <path d="M44 36c9-10 20-10 29 0-9 10-20 10-29 0Z" />
        <path d="M128 72l10 10m0-10-10 10" />
      </svg>
    </div>
  );
}

function handleAtmosphereMove(event: PointerEvent<HTMLElement>) {
  const bounds = event.currentTarget.getBoundingClientRect();
  const x = ((event.clientX - bounds.left) / bounds.width) * 100;
  const y = ((event.clientY - bounds.top) / bounds.height) * 100;
  event.currentTarget.style.setProperty("--pointer-x", `${x}%`);
  event.currentTarget.style.setProperty("--pointer-y", `${y}%`);
  event.currentTarget.style.setProperty("--pointer-dx", `${(x - 50) * -0.04}px`);
  event.currentTarget.style.setProperty("--pointer-dy", `${(y - 50) * -0.04}px`);
}

function resetAtmosphere(event: PointerEvent<HTMLElement>) {
  event.currentTarget.style.setProperty("--pointer-x", "50%");
  event.currentTarget.style.setProperty("--pointer-y", "35%");
  event.currentTarget.style.setProperty("--pointer-dx", "0px");
  event.currentTarget.style.setProperty("--pointer-dy", "0px");
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const activeHref = useActiveHref(pathname);

  return (
    <div className="flex min-h-full flex-1">
      <aside className="hidden w-60 shrink-0 flex-col gap-6 border-r bg-card px-4 py-6 sm:flex">
        <Link href="/" className="flex items-center gap-2 px-2">
          <ShieldIcon className="size-6 text-primary" />
          <span className="font-heading text-lg font-semibold">
            MCP Auditor
          </span>
        </Link>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.href} {...item} isActive={item.href === activeHref} />
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card px-4 py-3 sm:hidden">
          <Link href="/" className="flex items-center gap-2">
            <ShieldIcon className="size-5 text-primary" />
            <span className="font-heading font-semibold">MCP Auditor</span>
          </Link>
        </header>
        <nav className="flex gap-1 overflow-x-auto border-b bg-card px-2 py-2 sm:hidden">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.href} {...item} isActive={item.href === activeHref} />
          ))}
        </nav>

        <main
          className="app-main flex-1 bg-zinc-50 px-4 py-6 sm:px-8 sm:py-8 dark:bg-black"
          onPointerMove={handleAtmosphereMove}
          onPointerLeave={resetAtmosphere}
        >
          <AppAtmosphere />
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
