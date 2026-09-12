"use client";

import { useEffect, useState, useCallback } from "react";
import { CheckCircle, AlertOctagon, UserCog, ShieldCheck } from "lucide-react";
import { useAuth, withAuthHeader } from "@/lib/authContext";

interface Finding {
  id: string;
  work_id: number;
  control_id: string;
  problem_summary: string;
  severity: string;
  status: "OPEN" | "IN_REMEDIATION" | "RESOLVED";
  assigned_officer: string;
  required_action: string;
  deadline_date: string | null;
  detected_at: string | null;
  resolved_at: string | null;
  remediation_notes: string | null;
}

interface ResolutionRate {
  total_findings: number;
  resolved_count: number;
  resolution_rate: number | null;
  open_overdue_count: number;
}

const ACT_ALLOWED_ROLES = ["state_nodal", "district", "ministry"];

export default function ComplianceFindings() {
  const { user } = useAuth();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [rate, setRate] = useState<ResolutionRate | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [officers, setOfficers] = useState<Record<string, string>>({});

  const fetchAll = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const [fRes, rRes] = await Promise.all([
        fetch("/api/compliance/findings", { headers: withAuthHeader(user) }),
        fetch("/api/compliance/findings/resolution-rate", { headers: withAuthHeader(user) }),
      ]);
      const fJson = await fRes.json();
      const rJson = await rRes.json();
      if (fJson.success) setFindings(fJson.data.findings);
      if (rJson.success) setRate(rJson.data);
    } catch (err) {
      console.error("Failed to load findings:", err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  async function handleAssign(id: string) {
    const officer = officers[id]?.trim();
    if (!officer) return;
    setBusyId(id);
    try {
      const res = await fetch(`/api/compliance/findings/${id}/assign`, {
        method: "POST",
        headers: withAuthHeader(user, { "Content-Type": "application/json" }),
        body: JSON.stringify({ assigned_officer: officer }),
      });
      const json = await res.json();
      if (json.success) fetchAll();
      else alert(json.error);
    } finally {
      setBusyId(null);
    }
  }

  async function handleResolve(id: string) {
    const remediation_notes = notes[id]?.trim() || "Resolved.";
    setBusyId(id);
    try {
      const res = await fetch(`/api/compliance/findings/${id}/resolve`, {
        method: "POST",
        headers: withAuthHeader(user, { "Content-Type": "application/json" }),
        body: JSON.stringify({ remediation_notes }),
      });
      const json = await res.json();
      if (json.success) fetchAll();
      else alert(json.error);
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center animate-pulse text-xs text-slate-500 font-medium">Loading compliance findings...</div>;
  }

  const canAct = user ? ACT_ALLOWED_ROLES.includes(user.role) : false;
  const openFindings = findings.filter((f) => f.status !== "RESOLVED");
  const resolvedFindings = findings.filter((f) => f.status === "RESOLVED");

  return (
    <div className="space-y-4 font-body">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-black font-headline text-slate-900">Compliance Findings</h2>
          <p className="text-xs text-slate-500 font-medium">
            Trackable cases opened automatically on BLOCK-severity violations — flag → assign → resolve.
          </p>
        </div>
        {rate && (
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span className="font-bold text-slate-700">
              {rate.resolution_rate !== null ? `${(rate.resolution_rate * 100).toFixed(0)}% resolved` : "No findings yet"}
            </span>
            <span className="text-slate-400">({rate.resolved_count}/{rate.total_findings})</span>
            {rate.open_overdue_count > 0 && (
              <span className="rounded-full bg-rose-100 px-2 py-0.5 font-bold text-rose-700">{rate.open_overdue_count} overdue</span>
            )}
          </div>
        )}
      </div>

      {findings.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center space-y-2">
          <CheckCircle className="mx-auto h-10 w-10 text-emerald-500" />
          <h3 className="text-sm font-black text-slate-900">No findings open.</h3>
          <p className="text-xs text-slate-500">Nothing has tripped a BLOCK-severity rule yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {[...openFindings, ...resolvedFindings].map((f) => {
            const overdue = f.status !== "RESOLVED" && f.deadline_date && new Date(f.deadline_date) < new Date();
            return (
              <div key={f.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-black text-rose-700">{f.severity}</span>
                  <span className="font-mono text-xs font-bold text-slate-400">{f.id}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-black ${
                      f.status === "RESOLVED"
                        ? "bg-emerald-100 text-emerald-700"
                        : f.status === "IN_REMEDIATION"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {f.status.replace("_", " ")}
                  </span>
                  {overdue && (
                    <span className="flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-black text-rose-700">
                      <AlertOctagon className="h-3 w-3" /> OVERDUE
                    </span>
                  )}
                </div>

                <p className="mt-2 text-xs font-semibold text-slate-700">{f.problem_summary}</p>
                <p className="mt-1 text-[11px] text-slate-500">{f.required_action}</p>

                <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-100 pt-3 text-[11px] font-semibold text-slate-500">
                  <span>Work #{f.work_id}</span>
                  <span className="flex items-center gap-1"><UserCog className="h-3 w-3" /> {f.assigned_officer}</span>
                  <span>Deadline: {f.deadline_date}</span>
                  {f.resolved_at && <span className="text-emerald-600">Resolved {f.resolved_at}</span>}
                </div>
                {f.remediation_notes && (
                  <p className="mt-2 rounded-lg bg-slate-50 p-2 text-[11px] text-slate-600">{f.remediation_notes}</p>
                )}

                {canAct && f.status !== "RESOLVED" && (
                  <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
                    <input
                      placeholder="Reassign to..."
                      value={officers[f.id] || ""}
                      onChange={(e) => setOfficers({ ...officers, [f.id]: e.target.value })}
                      className="flex-1 min-w-[140px] rounded-lg border px-2 py-1 text-xs"
                    />
                    <button
                      disabled={busyId === f.id}
                      onClick={() => handleAssign(f.id)}
                      className="rounded-lg border px-3 py-1 text-xs font-bold text-primary disabled:opacity-50"
                    >
                      Assign
                    </button>
                    <input
                      placeholder="Remediation notes..."
                      value={notes[f.id] || ""}
                      onChange={(e) => setNotes({ ...notes, [f.id]: e.target.value })}
                      className="flex-1 min-w-[140px] rounded-lg border px-2 py-1 text-xs"
                    />
                    <button
                      disabled={busyId === f.id}
                      onClick={() => handleResolve(f.id)}
                      className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-bold text-white disabled:opacity-50"
                    >
                      Resolve
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
