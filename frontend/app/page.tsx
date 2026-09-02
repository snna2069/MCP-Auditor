"use client";

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
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          Audit Model Context Protocol servers for safety, permission, and
          reliability risks.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Registered servers"
          value={servers.data?.length ?? 0}
          isLoading={servers.isLoading}
        />
        <StatCard
          label="Total audits"
          value={audits.data?.length ?? 0}
          isLoading={audits.isLoading}
        />
        <StatCard
          label="High/critical risk"
          value={highRiskCount}
          isLoading={audits.isLoading}
        />
        <Card size="sm">
          <CardHeader>
            <CardDescription>Backend</CardDescription>
            <CardTitle className="text-2xl">
              {health.isLoading && "-"}
              {health.isError && (
                <Badge variant="destructive">Unreachable</Badge>
              )}
              {health.data && <Badge variant="secondary">Online</Badge>}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button nativeButton={false} render={<Link href="/servers/new" />}>
          Register a new server
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

      <Card>
        <CardHeader>
          <CardTitle>Recent audits</CardTitle>
          <CardDescription>The five most recently created audits.</CardDescription>
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
                <li key={audit.id} className="flex items-center justify-between py-2.5">
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
    </div>
  );
}
