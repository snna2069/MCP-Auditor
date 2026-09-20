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

export async function downloadAuditJsonReport(auditId: string): Promise<void> {
  const { data } = await apiClient.get<Blob>(`/audits/${auditId}/report`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = `audit-${auditId}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function openAuditHtmlReport(auditId: string): Promise<void> {
  const { data } = await apiClient.get<Blob>(`/audits/${auditId}/report/html`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(data);
  const reportWindow = window.open(url, "_blank", "noopener,noreferrer");
  if (!reportWindow) {
    URL.revokeObjectURL(url);
    throw new Error("The HTML report could not be opened in a new tab.");
  }
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
