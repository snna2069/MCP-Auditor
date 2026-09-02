import { RiskLevelBadge } from "@/components/shared/badges";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { RiskLevel } from "@/lib/types";

const RISK_COLOR: Record<RiskLevel, string> = {
  LOW: "bg-emerald-500",
  MODERATE: "bg-amber-500",
  HIGH: "bg-orange-500",
  CRITICAL: "bg-red-600",
};

export function ScoreSummary({
  overallScore,
  riskLevel,
}: {
  overallScore: number | null;
  riskLevel: RiskLevel | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Overall Score</CardTitle>
        <CardDescription>
          Starts at 100 and is reduced by weighted findings; never below 0.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-baseline gap-3">
          <span className="text-4xl font-semibold tabular-nums">
            {overallScore ?? "-"}
          </span>
          <RiskLevelBadge level={riskLevel} />
        </div>
        {overallScore !== null && (
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full transition-all ${riskLevel ? RISK_COLOR[riskLevel] : "bg-primary"}`}
              style={{ width: `${Math.min(100, Math.max(0, overallScore))}%` }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
