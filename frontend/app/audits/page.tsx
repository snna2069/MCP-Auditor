import { AuditTable } from "@/components/audits/audit-table";

export default function AuditsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Audit History
        </h1>
        <p className="mt-1 text-muted-foreground">
          All audits triggered across every registered server.
        </p>
      </div>

      <AuditTable />
    </div>
  );
}
