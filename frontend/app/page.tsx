"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useHealth } from "@/hooks/use-health";

export default function Home() {
  const { data, isLoading, isError } = useHealth();

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-black">
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-8 py-16">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            MCP Server Auditor
          </h1>
          <p className="mt-2 text-muted-foreground">
            Audit Model Context Protocol servers for safety, permission, and
            reliability risks.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Backend status</CardTitle>
            <CardDescription>
              Connectivity check against the FastAPI <code>/health</code>{" "}
              endpoint.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading && (
              <Badge variant="outline">Checking connection…</Badge>
            )}
            {isError && <Badge variant="destructive">Unreachable</Badge>}
            {data && (
              <div className="flex flex-col gap-2">
                <Badge variant="secondary">{data.status.toUpperCase()}</Badge>
                <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm text-muted-foreground">
                  <dt>App</dt>
                  <dd>{data.app_name}</dd>
                  <dt>Version</dt>
                  <dd>{data.version}</dd>
                  <dt>Environment</dt>
                  <dd>{data.environment}</dd>
                </dl>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
