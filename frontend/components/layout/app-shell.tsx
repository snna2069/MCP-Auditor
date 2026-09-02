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
import type { ReactNode } from "react";

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

        <main className="flex-1 bg-zinc-50 px-4 py-6 sm:px-8 sm:py-8 dark:bg-black">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
