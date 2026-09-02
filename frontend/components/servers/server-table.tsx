"use client";

import Link from "next/link";

import { DeleteServerDialog } from "@/components/servers/delete-server-dialog";
import {
  RunAuditButton,
  ServerToolsSheet,
  useToolsSheetState,
} from "@/components/servers/server-tools-sheet";
import {
  DiscoveryStatusBadge,
  SourceTypeBadge,
} from "@/components/shared/badges";
import {
  EmptyState,
  ErrorState,
  InlineSpinner,
  LoadingState,
} from "@/components/shared/state-views";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDiscoverServer, useServers } from "@/hooks/use-servers";
import type { MCPServer } from "@/lib/types";

function formatDate(value: string | null): string {
  if (!value) return "Never";
  return new Date(value).toLocaleString();
}

function DiscoverButton({ serverId }: { serverId: string }) {
  const { mutate, isPending } = useDiscoverServer();
  return (
    <Button
      size="sm"
      variant="outline"
      disabled={isPending}
      onClick={() => mutate(serverId)}
    >
      {isPending ? <InlineSpinner label="Discovering..." /> : "Discover"}
    </Button>
  );
}

export function ServerTable() {
  const { data: servers, isLoading, isError, refetch } = useServers();
  const toolsSheet = useToolsSheetState();

  if (isLoading) return <LoadingState rows={4} />;
  if (isError) {
    return (
      <ErrorState
        message="Could not load registered servers."
        onRetry={() => refetch()}
      />
    );
  }
  if (!servers || servers.length === 0) {
    return (
      <EmptyState
        title="No servers registered yet"
        description="Register an MCP server to start auditing it."
        action={
          <Button nativeButton={false} render={<Link href="/servers/new" />}>
            Register a server
          </Button>
        }
      />
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Last Discovery</TableHead>
            <TableHead>Discovered At</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {servers.map((server: MCPServer) => (
            <TableRow key={server.id}>
              <TableCell className="font-medium">{server.name}</TableCell>
              <TableCell>
                <SourceTypeBadge sourceType={server.source_type} />
              </TableCell>
              <TableCell>
                <DiscoveryStatusBadge status={server.last_discovery_status} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatDate(server.last_discovered_at)}
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap justify-end gap-2">
                  <DiscoverButton serverId={server.id} />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toolsSheet.openFor(server)}
                  >
                    View Tools
                  </Button>
                  <RunAuditButton serverId={server.id} />
                  <DeleteServerDialog server={server} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <ServerToolsSheet
        server={toolsSheet.server}
        open={toolsSheet.open}
        onOpenChange={toolsSheet.onOpenChange}
      />
    </>
  );
}
