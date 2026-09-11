import { ServerCogIcon } from "lucide-react";
import Link from "next/link";

import { PageReveal } from "@/components/shared/motion";
import { ServerTable } from "@/components/servers/server-table";
import { Button } from "@/components/ui/button";

export default function ServersPage() {
  return (
    <PageReveal>
    <div className="flex flex-col gap-6">
      <div className="page-heading flex items-center justify-between">
        <div>
          <div className="page-kicker"><ServerCogIcon /> MCP inventory</div>
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
    </PageReveal>
  );
}
