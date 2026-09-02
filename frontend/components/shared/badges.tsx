import { Badge } from "@/components/ui/badge";
import type {
  AuditStatus,
  DiscoveryStatus,
  RiskLevel,
  Severity,
  SourceType,
} from "@/lib/types";

export function RiskLevelBadge({ level }: { level: RiskLevel | null }) {
  if (!level) {
    return <Badge variant="outline">-</Badge>;
  }
  const variant = {
    LOW: "secondary",
    MODERATE: "outline",
    HIGH: "destructive",
    CRITICAL: "destructive",
  } as const;
  return <Badge variant={variant[level]}>{level}</Badge>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const variant = {
    INFO: "outline",
    LOW: "secondary",
    MEDIUM: "outline",
    HIGH: "destructive",
    CRITICAL: "destructive",
  } as const;
  return <Badge variant={variant[severity]}>{severity}</Badge>;
}

export function AuditStatusBadge({ status }: { status: AuditStatus }) {
  const variant = {
    PENDING: "outline",
    RUNNING: "secondary",
    COMPLETED: "secondary",
    FAILED: "destructive",
  } as const;
  return <Badge variant={variant[status]}>{status}</Badge>;
}

export function DiscoveryStatusBadge({
  status,
}: {
  status: DiscoveryStatus | null;
}) {
  if (!status) {
    return <Badge variant="outline">Never discovered</Badge>;
  }
  return (
    <Badge variant={status === "SUCCESS" ? "secondary" : "destructive"}>
      {status}
    </Badge>
  );
}

export function SourceTypeBadge({ sourceType }: { sourceType: SourceType }) {
  return <Badge variant="outline">{sourceType}</Badge>;
}
