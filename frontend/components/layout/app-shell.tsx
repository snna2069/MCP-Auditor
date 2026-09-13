"use client";

import {
  BotIcon,
  ClipboardListIcon,
  NetworkIcon,
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
        "group/nav flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
        isActive
          ? "bg-primary text-primary-foreground shadow-[0_8px_24px_-12px_oklch(0.32_0.12_250_/_0.85)]"
          : "text-muted-foreground hover:translate-x-0.5 hover:bg-muted hover:text-foreground",
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

function AppAtmosphere({ showCartoon = true }: { showCartoon?: boolean }) {
  return (
    <div aria-hidden="true" className="app-atmosphere">
      <div className="app-atmosphere-grid" />
      {showCartoon && (
        <svg className="app-cartoon app-cartoon-top" viewBox="0 0 190 150" fill="none">
          <path className="app-cartoon-line" d="M95 29V17m0 0-7 7m7-7 7 7" />
          <rect className="app-cartoon-body" x="46" y="30" width="98" height="83" rx="24" />
          <path className="app-cartoon-screen" d="M67 52h56v28H67z" />
          <circle className="app-cartoon-accent" cx="82" cy="66" r="5" />
          <circle className="app-cartoon-accent" cx="108" cy="66" r="5" />
          <path className="app-cartoon-line" d="M82 94h26m-42 19v16m56-16v16M46 67H31m113 0h15" />
          <circle className="app-cartoon-node" cx="22" cy="67" r="8" />
          <circle className="app-cartoon-node" cx="168" cy="67" r="8" />
          <path className="app-cartoon-line" d="m30 67 16 0m114 0h-16" />
        </svg>
      )}
      <svg className="app-network" viewBox="0 0 330 210" fill="none">
        <path d="M45 146 128 61l78 73 76-86" />
        <path d="m128 61 78 73m0 0 60 22" />
        <circle cx="45" cy="146" r="8" />
        <circle cx="128" cy="61" r="10" />
        <circle cx="206" cy="134" r="8" />
        <circle cx="282" cy="48" r="10" />
        <circle cx="266" cy="156" r="6" />
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
      <aside className="relative hidden w-64 shrink-0 flex-col gap-7 overflow-hidden border-r bg-card/90 px-4 py-6 backdrop-blur sm:flex">
        <div aria-hidden="true" className="sidebar-glow" />
        <Link href="/" className="relative flex items-center gap-2.5 px-2">
          <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
            <ShieldIcon className="size-5" />
          </span>
          <span>
            <span className="font-heading block text-lg font-semibold tracking-tight">
              MCP Auditor
            </span>
            <span className="flex items-center gap-1 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              <BotIcon className="size-3" /> AI security
            </span>
          </span>
        </Link>
        <div className="relative flex items-center gap-2 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          <NetworkIcon className="size-3" /> Workspace
        </div>
        <nav className="relative flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.href} {...item} isActive={item.href === activeHref} />
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card/90 px-4 py-3 backdrop-blur sm:hidden">
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
          className="app-main flex-1 px-4 py-6 sm:px-8 sm:py-8"
          onPointerMove={handleAtmosphereMove}
          onPointerLeave={resetAtmosphere}
        >
          <AppAtmosphere showCartoon={pathname !== "/servers"} />
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
