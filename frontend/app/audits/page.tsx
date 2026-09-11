import { RadarIcon } from "lucide-react";

import { AuditTable } from "@/components/audits/audit-table";
import { PageReveal } from "@/components/shared/motion";

export default function AuditsPage() {
  return (
    <PageReveal>
    <div className="flex flex-col gap-6">
      <div className="page-heading">
        <div className="page-kicker"><RadarIcon /> Risk intelligence</div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Audit History
        </h1>
        <p className="mt-1 text-muted-foreground">
          All audits triggered across every registered server.
        </p>
      </div>

      <AuditTable />
    </div>
    </PageReveal>
  );
}
