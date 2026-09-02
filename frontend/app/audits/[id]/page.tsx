import { AuditDetailView } from "@/components/audits/audit-detail-view";

export default async function AuditDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AuditDetailView auditId={id} />;
}
