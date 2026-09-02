import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createAudit, getAudit, listAuditFindings, listAudits } from "@/lib/api/audits";
import { queryKeys } from "@/lib/query-keys";
import { ACTIVE_AUDIT_STATUSES, type AuditDetail } from "@/lib/types";

const POLL_INTERVAL_MS = 2_000;

export function useAudits(serverId?: string) {
  return useQuery({
    queryKey: queryKeys.audits.all(serverId),
    queryFn: () => listAudits(serverId),
  });
}

/** Polls automatically while the audit is still PENDING/RUNNING so the
 * Audit Details page updates itself without a manual refresh. */
export function useAudit(auditId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.audits.detail(auditId ?? ""),
    queryFn: () => getAudit(auditId as string),
    enabled: Boolean(auditId),
    refetchInterval: (query) => {
      const data = query.state.data as AuditDetail | undefined;
      if (data && ACTIVE_AUDIT_STATUSES.includes(data.status)) {
        return POLL_INTERVAL_MS;
      }
      return false;
    },
  });
}

export function useAuditFindings(auditId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.audits.findings(auditId ?? ""),
    queryFn: () => listAuditFindings(auditId as string),
    enabled: Boolean(auditId) && enabled,
  });
}

export function useCreateAudit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serverId: string) => createAudit(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });
}
