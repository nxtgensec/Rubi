"use client";

import { PhoneCall } from "lucide-react";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiPath } from "@/lib/api";

type DialState = "idle" | "calling" | "success" | "error";

function normalizePhoneNumber(value: string) {
  const trimmed = value.trim().replace(/[^\d+]/g, "");
  if (!trimmed) {
    return "";
  }
  if (trimmed.startsWith("+")) {
    return trimmed;
  }
  if (trimmed.length === 10) {
    return `+91${trimmed}`;
  }
  return `+${trimmed}`;
}

export function OutboundCallPanel() {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [state, setState] = useState<DialState>("idle");
  const [message, setMessage] = useState("Enter a verified or callable number with country code.");

  async function startCall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const toNumber = normalizePhoneNumber(phoneNumber);

    if (!/^\+\d{10,15}$/.test(toNumber)) {
      setState("error");
      setMessage("Use a valid number like +917672010211 or 7672010211.");
      return;
    }

    setState("calling");
    setMessage(`Calling ${toNumber}...`);

    try {
      const response = await fetch(apiPath("/api/v1/twilio/outbound"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_number: toNumber,
          from_number: "+14244963973",
          preferred_language: "te-IN",
        }),
      });

      if (!response.ok) {
        throw new Error(await errorMessage(response));
      }

      const result = (await response.json()) as { provider_call_id?: string };
      setState("success");
      setMessage(`Call queued. Twilio ID: ${result.provider_call_id ?? "waiting"}`);
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Could not start the call.");
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Outbound Call</CardTitle>
        <CardDescription>Add a number and ask Rubi to call that person.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]" onSubmit={startCall}>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Phone number</span>
            <input
              className="h-10 min-w-0 rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-ring"
              inputMode="tel"
              onChange={(event) => setPhoneNumber(event.target.value)}
              placeholder="+91 76720 10211"
              type="tel"
              value={phoneNumber}
            />
          </label>
          <Button className="self-end" disabled={state === "calling"} type="submit">
            <PhoneCall className="h-4 w-4" />
            {state === "calling" ? "Calling" : "Call"}
          </Button>
        </form>
        <p
          className={
            state === "error"
              ? "mt-3 text-sm text-amber-500"
              : state === "success"
                ? "mt-3 text-sm text-primary"
                : "mt-3 text-sm text-muted-foreground"
          }
        >
          {message}
        </p>
      </CardContent>
    </Card>
  );
}

async function errorMessage(response: Response) {
  try {
    const data = (await response.json()) as { detail?: string };
    if (data.detail) {
      return data.detail;
    }
  } catch {
  }
  return `Call request failed with ${response.status}`;
}
