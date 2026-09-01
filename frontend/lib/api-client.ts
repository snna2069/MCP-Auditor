import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Shared axios instance for talking to the MCP Server Auditor backend.
 * Feature-specific clients (e.g. `lib/api/servers.ts` in later phases)
 * should build on top of this instance rather than creating their own.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});
