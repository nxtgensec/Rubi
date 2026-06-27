"use client";

import { Activity } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiPath, isApiConfigured } from "@/lib/api";

type VisitStats = {
  visit_date: string;
  today_visits: number;
  total_visits: number;
};

function getVisitorId() {
  const key = "rubi_visitor_id";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const id = crypto.randomUUID();
  window.localStorage.setItem(key, id);
  return id;
}

export function VisitorCounter() {
  const [stats, setStats] = useState<VisitStats | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "offline">("loading");
  const dateLabel = useMemo(() => stats?.visit_date ?? "today", [stats]);

  useEffect(() => {
    let active = true;

    async function fetchStats(method: "GET" | "POST") {
      if (!isApiConfigured()) {
        throw new Error("api url missing");
      }
      const path = `/api/v1/visits${method === "GET" ? `?t=${Date.now()}` : ""}`;
      const init: RequestInit =
        method === "POST"
          ? {
              method,
              headers: { "Content-Type": "application/json" },
              cache: "no-store",
              body: JSON.stringify({
                visitor_id: getVisitorId(),
                user_agent: navigator.userAgent,
              }),
            }
          : { method, cache: "no-store" };
      const response = await fetch(apiPath(path), init);
      if (!response.ok) throw new Error("visit request failed");
      return (await response.json()) as VisitStats;
    }

    async function recordVisit() {
      try {
        const data = await fetchStats("POST");
        if (active) {
          setStats(data);
          setStatus("ready");
        }
      } catch {
        if (active) setStatus("offline");
      }
    }

    async function refreshStats() {
      try {
        const data = await fetchStats("GET");
        if (active) {
          setStats(data);
          setStatus("ready");
        }
      } catch {
        if (active) setStatus("offline");
      }
    }

    refreshStats();
    recordVisit();
    const interval = window.setInterval(refreshStats, 5000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="fixed bottom-20 left-3 z-50 max-w-[calc(100vw-1.5rem)] rounded-lg border border-border bg-card/95 px-3 py-2 text-xs text-card-foreground shadow-lg backdrop-blur lg:bottom-3">
      <div className="flex items-center gap-2">
        <Activity className="h-3.5 w-3.5 text-primary" />
        <span className="font-medium">Visitors</span>
        <span className="text-muted-foreground">
          {status === "offline" ? "connection issue" : status === "loading" ? "syncing" : dateLabel}
        </span>
      </div>
      <div className="mt-1 grid grid-cols-2 gap-3 font-mono">
        <span>Today {stats?.today_visits ?? 0}</span>
        <span>Total {stats?.total_visits ?? 0}</span>
      </div>
    </div>
  );
}
