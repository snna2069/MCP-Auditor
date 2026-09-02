/** Centralized TanStack Query key factories, so keys never drift between
 * the hooks that read data and the mutations that invalidate it. */
export const queryKeys = {
  health: ["health"] as const,
  servers: {
    all: ["servers"] as const,
    detail: (id: string) => ["servers", id] as const,
    tools: (id: string) => ["servers", id, "tools"] as const,
  },
  audits: {
    all: (serverId?: string) => ["audits", { serverId }] as const,
    detail: (id: string) => ["audits", id] as const,
    findings: (id: string) => ["audits", id, "findings"] as const,
  },
};
