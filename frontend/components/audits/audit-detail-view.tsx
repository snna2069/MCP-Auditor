"use client";

import Link from "next/link";
import { useState } from "react";
import { isAxiosError } from "axios";
import {
  AlertCircleIcon,
  ChevronLeftIcon,
  DownloadIcon,
  ExternalLinkIcon,
} from "lucide-react";

import { CategoryBreakdown, SeverityBreakdown } from "@/components/audits/breakdowns";
import { FindingsTable } from "@/components/audits/findings-table";
import { ScoreSummary } from "@/components/audits/score-summary";
import { AuditStatusBadge } from "@/components/shared/badges";
import { ErrorState, InlineSpinner, LoadingState } from "@/components/shared/state-views";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAudit } from "@/hooks/use-audits";
import { useServer } from "@/hooks/use-servers";
import { downloadAuditJsonReport, openAuditHtmlReport } from "@/lib/api/audits";
import { ACTIVE_AUDIT_STATUSES } from "@/lib/types";

export function AuditDetailView({ auditId }: { auditId: string }) {
  const { data: audit, isLoading, isError, refetch } = useAudit(auditId);
  const { data: server } = useServer(audit?.server_id);
  const [reportAction, setReportAction] = useState<"json" | "html" | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const runReportAction = async (action: "json" | "html") => {
    setReportAction(action);
    setReportError(null);
    try {
      if (action === "json") {
        await downloadAuditJsonReport(auditId);
      } else {
        await openAuditHtmlReport(auditId);
      }
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        setReportError("This audit could not be found.");
      } else if (isAxiosError(error) && error.response?.status === 409) {
        setReportError("Reports are available after the audit completes.");
      } else if (error instanceof Error) {
        setReportError(error.message);
      } else {
        setReportError("Could not retrieve the audit report.");
      }
    } finally {
      setReportAction(null);
    }
  };

  if (isLoading) {
    return <LoadingState rows={6} />;
  }
  if (isError || !audit) {
    return (
      <ErrorState
        title="Could not load this audit"
        message="It may not exist, or the backend is unreachable."
        onRetry={() => refetch()}
      />
    );
  }

  const isActive = ACTIVE_AUDIT_STATUSES.includes(audit.status);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href="/audits"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeftIcon className="size-4" />
          Back to audit history
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">
            Audit {audit.id.slice(0, 8)}
          </h1>
          <AuditStatusBadge status={audit.status} />
        </div>
        <p className="mt-1 text-muted-foreground">
          Server: {server?.name ?? audit.server_id} &middot; Version{" "}
          {audit.audit_version} &middot; Created{" "}
          {new Date(audit.created_at).toLocaleString()}
        </p>
        {audit.status === "COMPLETED" && (
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={reportAction !== null}
              onClick={() => runReportAction("json")}
            >
              <DownloadIcon />
              {reportAction === "json" ? "Downloading..." : "Download JSON Report"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={reportAction !== null}
              onClick={() => runReportAction("html")}
            >
              <ExternalLinkIcon />
              {reportAction === "html" ? "Opening..." : "View HTML Report"}
            </Button>
          </div>
        )}
      </div>

      {reportError && (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Report unavailable</AlertTitle>
          <AlertDescription>{reportError}</AlertDescription>
        </Alert>
      )}

      {isActive && (
        <Alert>
          <InlineSpinner label="This audit is still running. This page updates automatically." />
        </Alert>
      )}

      {audit.status === "FAILED" && (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Audit failed</AlertTitle>
          <AlertDescription>
            {audit.error_message ?? "An unknown error occurred."}
          </AlertDescription>
        </Alert>
      )}

      {audit.status === "COMPLETED" && (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            <ScoreSummary
              overallScore={audit.overall_score}
              riskLevel={audit.risk_level}
            />
            {audit.severity_breakdown && (
              <SeverityBreakdown breakdown={audit.severity_breakdown} />
            )}
          </div>

          {audit.category_scores && (
            <CategoryBreakdown scores={audit.category_scores} />
          )}

          <Card>
            <CardHeader>
              <CardTitle>Findings</CardTitle>
              <CardDescription>
                Every issue identified across this server&apos;s tools.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FindingsTable auditId={audit.id} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
