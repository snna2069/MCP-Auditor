import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createServer,
  deleteServer,
  discoverServer,
  getServer,
  listServerTools,
  listServers,
} from "@/lib/api/servers";
import { queryKeys } from "@/lib/query-keys";
import type { CreateServerPayload } from "@/lib/types";

export function useServers() {
  return useQuery({
    queryKey: queryKeys.servers.all,
    queryFn: listServers,
  });
}

export function useServer(serverId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.servers.detail(serverId ?? ""),
    queryFn: () => getServer(serverId as string),
    enabled: Boolean(serverId),
  });
}

export function useServerTools(serverId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.servers.tools(serverId ?? ""),
    queryFn: () => listServerTools(serverId as string),
    enabled: Boolean(serverId),
  });
}

export function useCreateServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateServerPayload) => createServer(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.servers.all });
    },
  });
}

export function useDeleteServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serverId: string) => deleteServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.servers.all });
    },
  });
}

export function useDiscoverServer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serverId: string) => discoverServer(serverId),
    onSuccess: (_result, serverId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.servers.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.servers.tools(serverId),
      });
    },
  });
}
