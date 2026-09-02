"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { EmptyState, ErrorState, InlineSpinner, LoadingState } from "@/components/shared/state-views";
import { useCreateAudit } from "@/hooks/use-audits";
import { useServerTools } from "@/hooks/use-servers";
import type { MCPServer } from "@/lib/types";
import { useRouter } from "next/navigation";

export function ServerToolsSheet({
  server,
  open,
  onOpenChange,
}: {
  server: MCPServer | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: tools, isLoading, isError, refetch } = useServerTools(
    server?.id,
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{server?.name ?? "Server"} tools</SheetTitle>
          <SheetDescription>
            Most recently discovered tools. Run discovery again from the
            registry to refresh this list.
          </SheetDescription>
        </SheetHeader>
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          {isLoading && <LoadingState rows={4} />}
          {isError && (
            <ErrorState
              message="Could not load tools for this server."
              onRetry={() => refetch()}
            />
          )}
          {tools && tools.length === 0 && (
            <EmptyState
              title="No tools discovered yet"
              description="Use the Discover action on the registry to fetch this server's tools."
            />
          )}
          {tools && tools.length > 0 && (
            <ul className="flex flex-col gap-3">
              {tools.map((tool) => (
                <li
                  key={tool.id}
                  className="rounded-lg border p-3 text-sm"
                >
                  <p className="font-medium">{tool.title ?? tool.name}</p>
                  <p className="text-xs text-muted-foreground">{tool.name}</p>
                  {tool.description && (
                    <p className="mt-1 text-muted-foreground">
                      {tool.description}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function RunAuditButton({ serverId }: { serverId: string }) {
  const router = useRouter();
  const { mutate, isPending } = useCreateAudit();

  return (
    <Button
      size="sm"
      variant="outline"
      disabled={isPending}
      onClick={() =>
        mutate(serverId, {
          onSuccess: (audit) => router.push(`/audits/${audit.id}`),
        })
      }
    >
      {isPending ? <InlineSpinner label="Starting..." /> : "Run Audit"}
    </Button>
  );
}

export function useToolsSheetState() {
  const [server, setServer] = useState<MCPServer | null>(null);
  return {
    server,
    open: server !== null,
    onOpenChange: (open: boolean) => {
      if (!open) setServer(null);
    },
    openFor: setServer,
  };
}
