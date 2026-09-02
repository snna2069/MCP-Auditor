"use client";

import Link from "next/link";
import { useState } from "react";

import { AuditStatusBadge, RiskLevelBadge } from "@/components/shared/badges";
import {
  EmptyState,
  ErrorState,
  InlineSpinner,
  LoadingState,
} from "@/components/shared/state-views";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAudits, useCreateAudit } from "@/hooks/use-audits";
import { useServers } from "@/hooks/use-servers";

function NewAuditControl() {
  const { data: servers } = useServers();
  const [selected, setSelected] = useState<string | null>(null);
  const { mutate, isPending } = useCreateAudit();

  if (!servers || servers.length === 0) return null;

  const selectedServerName = servers.find((s) => s.id === selected)?.name;

  return (
    <div className="flex items-center gap-2">
      <Select value={selected} onValueChange={(value) => setSelected(value)}>
        <SelectTrigger className="w-56">
          <SelectValue placeholder="Select a server...">
            {selectedServerName ?? "Select a server..."}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {servers.map((server) => (
            <SelectItem key={server.id} value={server.id}>
              {server.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        disabled={!selected || isPending}
        onClick={() => selected && mutate(selected)}
      >
        {isPending ? <InlineSpinner label="Starting..." /> : "Run Audit"}
      </Button>
    </div>
  );
}

export function AuditTable({ serverId }: { serverId?: string }) {
  const { data: servers } = useServers();
  const { data: audits, isLoading, isError, refetch } = useAudits(serverId);

  const serverName = (id: string) =>
    servers?.find((s) => s.id === id)?.name ?? id.slice(0, 8);

  return (
    <div className="flex flex-col gap-4">
      <NewAuditControl />

      {isLoading && <LoadingState rows={4} />}
      {isError && (
        <ErrorState
          message="Could not load audit history."
          onRetry={() => refetch()}
        />
      )}
      {audits && audits.length === 0 && (
        <EmptyState
          title="No audits yet"
          description="Trigger an audit above or from the Server Registry."
        />
      )}
      {audits && audits.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Server</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Risk Level</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {audits.map((audit) => (
              <TableRow key={audit.id}>
                <TableCell className="font-medium">
                  {serverName(audit.server_id)}
                </TableCell>
                <TableCell>
                  <AuditStatusBadge status={audit.status} />
                </TableCell>
                <TableCell>
                  <RiskLevelBadge level={audit.risk_level} />
                </TableCell>
                <TableCell>{audit.overall_score ?? "-"}</TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(audit.created_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    nativeButton={false}
                    render={<Link href={`/audits/${audit.id}`} />}
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
