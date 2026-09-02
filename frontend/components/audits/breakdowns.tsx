import { SeverityBadge } from "@/components/shared/badges";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AuditCategory, Severity } from "@/lib/types";

const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

export function SeverityBreakdown({
  breakdown,
}: {
  breakdown: Partial<Record<Severity, number>>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Severity Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-2">
          {SEVERITY_ORDER.map((severity) => (
            <div
              key={severity}
              className="flex flex-col items-center gap-1.5 rounded-lg border p-2.5"
            >
              <span className="text-xl font-semibold tabular-nums">
                {breakdown[severity] ?? 0}
              </span>
              <SeverityBadge severity={severity} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

const CATEGORY_LABELS: Record<AuditCategory, string> = {
  TOOL_DEFINITION_QUALITY: "Tool Definition Quality",
  CAPABILITY_PERMISSION_RISK: "Capability & Permission Risk",
  PROMPT_INJECTION_RISK: "Prompt Injection Risk",
  HALLUCINATION_RELIABILITY_RISK: "Hallucination & Reliability Risk",
  SIDE_EFFECT_ANALYSIS: "Side Effect Analysis",
};

export function CategoryBreakdown({
  scores,
}: {
  scores: Partial<Record<AuditCategory, number>>;
}) {
  const entries = Object.entries(scores) as [AuditCategory, number][];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3">
          {entries.map(([category, score]) => (
            <li key={category} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-sm">
                <span>{CATEGORY_LABELS[category]}</span>
                <span className="font-medium tabular-nums">{score}</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
