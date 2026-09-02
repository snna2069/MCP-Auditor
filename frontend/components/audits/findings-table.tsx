"use client";

import { useState } from "react";

import { SeverityBadge } from "@/components/shared/badges";
import { EmptyState, ErrorState, LoadingState } from "@/components/shared/state-views";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuditFindings } from "@/hooks/use-audits";
import type { AuditFinding } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  TOOL_DEFINITION_QUALITY: "Tool Definition Quality",
  CAPABILITY_PERMISSION_RISK: "Capability & Permission Risk",
  PROMPT_INJECTION_RISK: "Prompt Injection Risk",
  HALLUCINATION_RELIABILITY_RISK: "Hallucination & Reliability Risk",
  SIDE_EFFECT_ANALYSIS: "Side Effect Analysis",
};

function FindingDetailSheet({
  finding,
  onOpenChange,
}: {
  finding: AuditFinding | null;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={finding !== null} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{finding?.title}</SheetTitle>
          <SheetDescription>
            {finding && CATEGORY_LABELS[finding.category]} &middot; Tool:{" "}
            {finding?.tool_name}
          </SheetDescription>
        </SheetHeader>
        {finding && (
          <div className="flex flex-col gap-4 overflow-y-auto px-4 pb-4 text-sm">
            <div className="flex items-center gap-2">
              <SeverityBadge severity={finding.severity} />
            </div>
            <section>
              <h3 className="mb-1 font-medium">Description</h3>
              <p className="text-muted-foreground">{finding.description}</p>
            </section>
            <section>
              <h3 className="mb-1 font-medium">Recommendation</h3>
              <p className="text-muted-foreground">{finding.recommendation}</p>
            </section>
            <section>
              <h3 className="mb-1 font-medium">Evidence</h3>
              <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-xs">
                {JSON.stringify(finding.evidence, null, 2)}
              </pre>
            </section>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

export function FindingsTable({ auditId }: { auditId: string }) {
  const { data: findings, isLoading, isError, refetch } = useAuditFindings(auditId);
  const [selected, setSelected] = useState<AuditFinding | null>(null);

  if (isLoading) return <LoadingState rows={4} />;
  if (isError) {
    return (
      <ErrorState
        message="Could not load findings for this audit."
        onRetry={() => refetch()}
      />
    );
  }
  if (!findings || findings.length === 0) {
    return (
      <EmptyState
        title="No findings"
        description="This tool set looks clean - no issues were detected."
      />
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Severity</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Tool</TableHead>
            <TableHead>Finding</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {findings.map((finding) => (
            <TableRow key={finding.id}>
              <TableCell>
                <SeverityBadge severity={finding.severity} />
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {CATEGORY_LABELS[finding.category]}
              </TableCell>
              <TableCell className="font-mono text-xs">
                {finding.tool_name}
              </TableCell>
              <TableCell>{finding.title}</TableCell>
              <TableCell className="text-right">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelected(finding)}
                >
                  View
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <FindingDetailSheet
        finding={selected}
        onOpenChange={(open) => !open && setSelected(null)}
      />
    </>
  );
}
