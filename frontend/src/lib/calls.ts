import { apiPath, isApiConfigured } from "@/lib/api";

export type Call = {
  id: string;
  caller: string;
  language: string;
  status: string;
  recording_status: string;
  recording_url: string | null;
  summary: string;
  sentiment: string;
  transcript: string[];
  started_at: string;
};

export async function getCalls(): Promise<Call[]> {
  if (!isApiConfigured()) {
    return [];
  }
  try {
    const response = await fetch(apiPath("/api/v1/calls"), { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    return [];
  }
}

export function recordingUrl(callId: string) {
  return apiPath(`/api/v1/calls/${callId}/recording`);
}

export function formatCallTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
