import { apiClient } from "@/lib/api-client";
import type {
  CreateServerPayload,
  DiscoveryResult,
  MCPServer,
  ToolProfile,
} from "@/lib/types";

export async function listServers(): Promise<MCPServer[]> {
  const { data } = await apiClient.get<MCPServer[]>("/servers", {
    params: { limit: 200 },
  });
  return data;
}

export async function getServer(serverId: string): Promise<MCPServer> {
  const { data } = await apiClient.get<MCPServer>(`/servers/${serverId}`);
  return data;
}

export async function createServer(
  payload: CreateServerPayload,
): Promise<MCPServer> {
  const { data } = await apiClient.post<MCPServer>("/servers", payload);
  return data;
}

export async function deleteServer(serverId: string): Promise<void> {
  await apiClient.delete(`/servers/${serverId}`);
}

export async function discoverServer(
  serverId: string,
): Promise<DiscoveryResult> {
  const { data } = await apiClient.post<DiscoveryResult>(
    `/servers/${serverId}/discover`,
  );
  return data;
}

export async function listServerTools(
  serverId: string,
): Promise<ToolProfile[]> {
  const { data } = await apiClient.get<ToolProfile[]>(
    `/servers/${serverId}/tools`,
  );
  return data;
}
