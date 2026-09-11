import { PlusIcon } from "lucide-react";

import { NewServerForm } from "@/components/servers/new-server-form";
import { PageReveal } from "@/components/shared/motion";
import { Card, CardContent } from "@/components/ui/card";

export default function NewServerPage() {
  return (
    <PageReveal>
    <div className="flex flex-col gap-6">
      <div className="page-heading">
        <div className="page-kicker"><PlusIcon /> Expand coverage</div>
        <h1 className="text-2xl font-semibold tracking-tight">New Server</h1>
        <p className="mt-1 text-muted-foreground">
          Register an MCP server configuration to audit later.
        </p>
      </div>

      <Card className="max-w-2xl">
        <CardContent className="pt-4">
          <NewServerForm />
        </CardContent>
      </Card>
    </div>
    </PageReveal>
  );
}
