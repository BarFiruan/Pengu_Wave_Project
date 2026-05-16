import { apiFetch } from "./client";
import type { SecurityEvent } from "../types";

export async function getEvents(params?: {
  severity?: string;
  search?: string;
}): Promise<SecurityEvent[]> {
  const query = new URLSearchParams();
  if (params?.severity && params.severity !== "ALL") {
    query.set("severity", params.severity);
  }
  if (params?.search) {
    query.set("search", params.search);
  }
  const qs = query.toString();
  return apiFetch(`/api/events${qs ? `?${qs}` : ""}`);
}

export async function getEvent(id: string): Promise<SecurityEvent> {
  return apiFetch(`/api/events/${id}`);
}
