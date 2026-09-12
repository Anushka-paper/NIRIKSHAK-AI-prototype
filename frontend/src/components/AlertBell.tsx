"use client";

import { useEffect, useState, useCallback } from "react";
import { Bell, CheckCircle2, AlertOctagon } from "lucide-react";
import { useAuth, withAuthHeader } from "@/lib/authContext";

interface AlertItem {
  id: number;
  work_id: number;
  rule_code: string;
  severity: string;
  message: string;
  created_at: string;
  read_at: string | null;
  resolved_at: string | null;
}

const RESOLVE_ALLOWED_ROLES = ["state_nodal", "district", "ministry"];

export default function AlertBell() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);

  const fetchAlerts = useCallback(async () => {
    if (!user) return;
    try {
      const res = await fetch("/api/alerts?unresolved_only=true", { headers: withAuthHeader(user) });
      const json = await res.json();
      if (json.success) {
        setAlerts(json.data.alerts);
        setUnreadCount(json.data.unread_count);
      }
    } catch {
      // best-effort — a failed alert fetch shouldn't break the page
    }
  }, [user]);

  useEffect(() => {
    fetchAlerts();
    // Poll every 30s so a newly-raised BLOCK alert shows up without a full page reload.
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  async function markRead(id: number) {
    await fetch(`/api/alerts/${id}/read`, { method: "POST", headers: withAuthHeader(user) });
    fetchAlerts();
  }

  async function resolve(id: number) {
    await fetch(`/api/alerts/${id}/resolve`, { method: "POST", headers: withAuthHeader(user) });
    fetchAlerts();
  }

  if (!user) return null;

  const canResolve = RESOLVE_ALLOWED_ROLES.includes(user.role);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-lg border p-1.5 text-gray-600 hover:text-primary"
        aria-label="Alerts"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1.5 -right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-xl border bg-white shadow-lg">
          <div className="border-b px-4 py-2 text-xs font-bold text-gray-600">
            Risk Alerts {alerts.length > 0 && `(${alerts.length})`}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {alerts.length === 0 && (
              <p className="px-4 py-6 text-center text-xs text-gray-400">No open alerts.</p>
            )}
            {alerts.map((a) => (
              <div key={a.id} className="border-b px-4 py-3 text-xs last:border-b-0">
                <div className="flex items-start gap-2">
                  <AlertOctagon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-500" />
                  <div className="flex-1">
                    <p className="font-bold text-slate-700">
                      Work #{a.work_id} &middot; {a.rule_code}
                    </p>
                    <p className="mt-0.5 text-gray-500">{a.message}</p>
                    <div className="mt-2 flex gap-3">
                      {!a.read_at && (
                        <button onClick={() => markRead(a.id)} className="font-bold text-primary hover:underline">
                          Mark read
                        </button>
                      )}
                      {canResolve && (
                        <button
                          onClick={() => resolve(a.id)}
                          className="flex items-center gap-1 font-bold text-emerald-600 hover:underline"
                        >
                          <CheckCircle2 className="h-3 w-3" /> Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
