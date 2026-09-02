import { NewServerForm } from "@/components/servers/new-server-form";

export default function NewServerPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New Server</h1>
        <p className="mt-1 text-muted-foreground">
          Register an MCP server configuration to audit later.
        </p>
      </div>

      <NewServerForm />
    </div>
  );
}
