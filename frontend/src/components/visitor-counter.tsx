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
    <div className="fixed bottom-[4.9rem] left-2 z-30 max-w-[calc(100vw-1rem)] rounded-md border border-border bg-card/95 px-2 py-1.5 text-[10px] text-card-foreground shadow-lg backdrop-blur sm:left-3 sm:px-3 sm:py-2 sm:text-xs lg:bottom-3">
      <div className="flex items-center gap-1.5 sm:gap-2">
        <Activity className="h-3 w-3 text-primary sm:h-3.5 sm:w-3.5" />
        <span className="font-medium">Visitors</span>
        <span className="hidden text-muted-foreground min-[380px]:inline">
          {status === "offline" ? "connection issue" : status === "loading" ? "syncing" : dateLabel}
        </span>
      </div>
      <div className="mt-0.5 grid grid-cols-2 gap-2 font-mono sm:mt-1 sm:gap-3">
        <span>Today {stats?.today_visits ?? 0}</span>
        <span>Total {stats?.total_visits ?? 0}</span>
      </div>
    </div>
  );
}
