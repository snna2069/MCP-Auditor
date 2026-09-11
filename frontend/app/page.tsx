"use client";

import { motion } from "framer-motion";
import {
  ArrowUpRightIcon,
  BotIcon,
  NetworkIcon,
  RadarIcon,
} from "lucide-react";
import Link from "next/link";

import { AuditStatusBadge, RiskLevelBadge } from "@/components/shared/badges";
import { EmptyState, ErrorState, LoadingState } from "@/components/shared/state-views";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAudits } from "@/hooks/use-audits";
import { useHealth } from "@/hooks/use-health";
import { useServers } from "@/hooks/use-servers";
import { RevealItem, StaggeredReveal } from "@/components/shared/motion";

function StatCard({
  label,
  value,
  isLoading,
}: {
  label: string;
  value: number | string;
  isLoading?: boolean;
}) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">
          {isLoading ? "-" : value}
        </CardTitle>
      </CardHeader>
    </Card>
  );
}

export default function DashboardPage() {
  const health = useHealth();
  const servers = useServers();
  const audits = useAudits();

  const recentAudits = (audits.data ?? []).slice(0, 5);
  const highRiskCount = (audits.data ?? []).filter(
    (a) => a.risk_level === "HIGH" || a.risk_level === "CRITICAL",
  ).length;

  return (
    <div className="dashboard-page relative isolate flex flex-col gap-6">
      <section className="relative overflow-hidden rounded-2xl border border-primary/15 bg-card/80 px-5 py-6 shadow-[0_20px_45px_-32px_oklch(0.3_0.12_250_/_0.55)] sm:px-7 sm:py-8">
        <div className="absolute -right-4 -top-8 opacity-90 sm:right-6">
          <svg className="size-40 text-primary/15 sm:size-48" viewBox="0 0 200 200" fill="none">
            <circle cx="100" cy="100" r="74" stroke="currentColor" strokeWidth="1.5" />
            <circle cx="100" cy="100" r="48" stroke="currentColor" strokeWidth="1" strokeDasharray="5 7" />
            <circle cx="100" cy="100" r="8" fill="currentColor" />
            <path d="M100 26v48m0 52v48M26 100h48m52 0h48M47 47l34 34m38 38 34 34M153 47l-34 34m-38 38-34 34" stroke="currentColor" strokeWidth="1.5" />
          </svg>
        </div>
        <div className="relative max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-700">
            <span className="size-1.5 animate-pulse rounded-full bg-emerald-500" />
            MCP control plane
          </div>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Secure every tool your <span className="text-primary">AI can reach.</span>
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
            Discover protocol capabilities, trace permission boundaries, and surface risk before your agents execute.
          </p>
          <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-muted-foreground">
            <span className="inline-flex items-center gap-1.5"><NetworkIcon className="size-3.5 text-primary" /> Protocol-aware scans</span>
            <span className="inline-flex items-center gap-1.5"><BotIcon className="size-3.5 text-primary" /> Agent-ready intelligence</span>
          </div>
        </div>
      </section>

      <StaggeredReveal>
        <div className="relative grid grid-cols-2 gap-3 sm:grid-cols-4">
          <RevealItem><StatCard label="Registered servers" value={servers.data?.length ?? 0} isLoading={servers.isLoading} /></RevealItem>
          <RevealItem><StatCard label="Total audits" value={audits.data?.length ?? 0} isLoading={audits.isLoading} /></RevealItem>
          <RevealItem><StatCard label="High/critical risk" value={highRiskCount} isLoading={audits.isLoading} /></RevealItem>
          <RevealItem>
            <Card size="sm">
              <CardHeader>
                <CardDescription>Backend</CardDescription>
                <CardTitle className="text-2xl">
                  {health.isLoading && "-"}
                  {health.isError && <Badge variant="destructive">Unreachable</Badge>}
                  {health.data && <Badge variant="secondary">Online</Badge>}
                </CardTitle>
              </CardHeader>
            </Card>
          </RevealItem>
        </div>
      </StaggeredReveal>

      <div className="relative flex flex-wrap gap-2">
        <Button nativeButton={false} render={<Link href="/servers/new" />}>
          Register a new server <ArrowUpRightIcon />
        </Button>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/servers" />}
        >
          View servers
        </Button>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href="/audits" />}
        >
          View audit history
        </Button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.35 }}
      >
        <Card className="relative">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RadarIcon className="size-4 text-primary" /> Recent audits
            </CardTitle>
            <CardDescription>
              The latest MCP security signals from your workspace.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {audits.isLoading && <LoadingState rows={3} />}
            {audits.isError && (
              <ErrorState
                message="Could not load recent audits."
                onRetry={() => audits.refetch()}
              />
            )}
            {audits.data && recentAudits.length === 0 && (
              <EmptyState
                title="No audits yet"
                description="Trigger an audit from the Server Registry to see results here."
              />
            )}
            {recentAudits.length > 0 && (
              <ul className="flex flex-col divide-y">
                {recentAudits.map((audit) => (
                  <li
                    key={audit.id}
                    className="flex items-center justify-between py-2.5"
                  >
                    <Link
                      href={`/audits/${audit.id}`}
                      className="flex flex-col hover:underline"
                    >
                      <span className="text-sm font-medium">
                        Audit {audit.id.slice(0, 8)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(audit.created_at).toLocaleString()}
                      </span>
                    </Link>
                    <div className="flex items-center gap-2">
                      <AuditStatusBadge status={audit.status} />
                      <RiskLevelBadge level={audit.risk_level} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
