import Link from "next/link";

import { ServerTable } from "@/components/servers/server-table";
import { Button } from "@/components/ui/button";

export default function ServersPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Server Registry
          </h1>
          <p className="mt-1 text-muted-foreground">
            MCP servers registered for auditing.
          </p>
        </div>
        <Button nativeButton={false} render={<Link href="/servers/new" />}>
          New server
        </Button>
      </div>

      <ServerTable />
    </div>
  );
}
