import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { HealthResponse } from "@/lib/types";

async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });
}
