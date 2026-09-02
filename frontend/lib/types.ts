export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
}

// --- Shared enums (mirrors backend/app/models/enums.py) ---

export type SourceType =
  | "LOCAL_COMMAND"
  | "HTTP"
  | "SSE"
  | "PACKAGE"
  | "MANUAL_CONFIGURATION";

/** Source types the ingestion API currently accepts (Phase 1). */
export const SUPPORTED_SOURCE_TYPES: SourceType[] = [
  "LOCAL_COMMAND",
  "HTTP",
  "MANUAL_CONFIGURATION",
];

export type DiscoveryStatus = "SUCCESS" | "FAILED";

export type AuditStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AuditCategory =
  | "TOOL_DEFINITION_QUALITY"
  | "CAPABILITY_PERMISSION_RISK"
  | "PROMPT_INJECTION_RISK"
  | "HALLUCINATION_RELIABILITY_RISK"
  | "SIDE_EFFECT_ANALYSIS";

// --- MCP servers (Phase 1/2) ---

export interface MCPServer {
  id: string;
  name: string;
  source_type: SourceType;
  connection_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_discovery_status: DiscoveryStatus | null;
  last_discovered_at: string | null;
  last_discovery_error: string | null;
}

export interface LocalCommandConfig {
  command: string;
  args: string[];
  env: Record<string, string>;
}

export interface HttpConfig {
  url: string;
  headers: Record<string, string>;
  timeout_seconds: number;
}

export interface ManualConfig {
  description: string | null;
  details: Record<string, unknown>;
}

export interface CreateServerPayload {
  name: string;
  source_type: SourceType;
  connection_config: Record<string, unknown>;
}

// --- Tool discovery (Phase 2) ---

export interface ToolAnnotations {
  title: string | null;
  read_only_hint: boolean | null;
  destructive_hint: boolean | null;
  idempotent_hint: boolean | null;
  open_world_hint: boolean | null;
}

export interface ToolProfile {
  id: string;
  name: string;
  title: string | null;
  description: string | null;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown> | null;
  annotations: ToolAnnotations | null;
  discovered_at: string;
}

export interface DiscoveryResult {
  status: DiscoveryStatus;
  error: string | null;
  discovered_at: string;
  tool_count: number;
  tools: ToolProfile[];
}

// --- Audits (Phase 5) ---

export interface Audit {
  id: string;
  server_id: string;
  status: AuditStatus;
  audit_version: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  overall_score: number | null;
  risk_level: RiskLevel | null;
  error_message: string | null;
}

export interface ScoreContributor {
  tool_name: string;
  category: AuditCategory;
  severity: Severity;
  title: string;
  severity_weight: number;
  category_weight: number;
  contribution: number;
}

export interface AuditDetail extends Audit {
  category_scores: Partial<Record<AuditCategory, number>> | null;
  severity_breakdown: Partial<Record<Severity, number>> | null;
  score_contributors: ScoreContributor[] | null;
}

export interface AuditFinding {
  id: string;
  audit_id: string;
  category: AuditCategory;
  severity: Severity;
  title: string;
  description: string;
  evidence: Record<string, unknown>;
  recommendation: string;
  tool_name: string;
  created_at: string;
}

/** The lifecycle states in which polling for updates makes sense. */
export const ACTIVE_AUDIT_STATUSES: AuditStatus[] = ["PENDING", "RUNNING"];
