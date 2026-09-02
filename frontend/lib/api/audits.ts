import { apiClient } from "@/lib/api-client";
import type { Audit, AuditDetail, AuditFinding } from "@/lib/types";

export async function listAudits(serverId?: string): Promise<Audit[]> {
  const { data } = await apiClient.get<Audit[]>("/audits", {
    params: { limit: 200, ...(serverId ? { server_id: serverId } : {}) },
  });
  return data;
}

export async function getAudit(auditId: string): Promise<AuditDetail> {
  const { data } = await apiClient.get<AuditDetail>(`/audits/${auditId}`);
  return data;
}

export async function createAudit(serverId: string): Promise<Audit> {
  const { data } = await apiClient.post<Audit>(`/servers/${serverId}/audits`);
  return data;
}

export async function listAuditFindings(
  auditId: string,
): Promise<AuditFinding[]> {
  const { data } = await apiClient.get<AuditFinding[]>(
    `/audits/${auditId}/findings`,
  );
  return data;
}
