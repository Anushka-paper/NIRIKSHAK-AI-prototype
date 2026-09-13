"use client";

import { useEffect, useState, useCallback } from "react";
import { useRequireAuth, withAuthHeader } from "@/lib/authContext";

interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  scope_id: string | null;
  status: "active" | "invited" | "disabled";
  created_at: string;
}

interface MpOption {
  id: number;
  name: string;
  constituency_name: string;
  state: string;
}

const ROLES = [
  { value: "mp", label: "Member of Parliament" },
  { value: "state_nodal", label: "State Nodal Authority" },
  { value: "district", label: "District Authority" },
  { value: "ministry", label: "Ministry" },
];

export default function AdminUsersPage() {
  const { user, loading: authLoading } = useRequireAuth(["ministry"]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [mps, setMps] = useState<MpOption[]>([]);
  const [form, setForm] = useState({ email: "", full_name: "", role: "mp", scope_id: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastInviteUrl, setLastInviteUrl] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    if (!user) return;
    const res = await fetch("/api/admin/users", { headers: withAuthHeader(user) });
    const json = await res.json();
    if (json.success) setUsers(json.data.users);
  }, [user]);

  const fetchMps = useCallback(async () => {
    if (!user) return;
    const res = await fetch("/api/admin/mps", { headers: withAuthHeader(user) });
    const json = await res.json();
    if (json.success) setMps(json.data.mps);
  }, [user]);

  useEffect(() => {
    fetchUsers();
    fetchMps();
  }, [fetchUsers, fetchMps]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLastInviteUrl(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: withAuthHeader(user, { "Content-Type": "application/json" }),
        body: JSON.stringify({
          ...form,
          scope_id: form.role === "ministry" ? null : form.scope_id,
        }),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      setLastInviteUrl(`${window.location.origin}${json.data.invite_url}`);
      setForm({ email: "", full_name: "", role: "mp", scope_id: "" });
      fetchUsers();
    } catch (err: any) {
      setError(err.message || "Failed to create account");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReinvite(userId: number) {
    const res = await fetch(`/api/admin/users/${userId}/reinvite`, {
      method: "POST",
      headers: withAuthHeader(user),
    });
    const json = await res.json();
    if (json.success) {
      setLastInviteUrl(`${window.location.origin}${json.data.invite_url}`);
    } else {
      alert(json.error);
    }
  }

  async function handleToggleActive(userId: number) {
    const res = await fetch(`/api/admin/users/${userId}/toggle-active`, {
      method: "POST",
      headers: withAuthHeader(user),
    });
    const json = await res.json();
    if (json.success) {
      fetchUsers();
    } else {
      alert(json.error);
    }
  }

  if (authLoading || !user) {
    return <div className="py-24 text-center text-sm text-gray-500">Loading...</div>;
  }

  const activeCount = users.filter((u) => u.status === "active").length;
  const invitedCount = users.filter((u) => u.status === "invited").length;
  const disabledCount = users.filter((u) => u.status === "disabled").length;

  return (
    <div className="mx-auto max-w-4xl space-y-8 py-6">
      <div>
        <h1 className="font-headline text-2xl font-extrabold text-primary">Provision accounts</h1>
        <p className="text-sm text-gray-500">
          Create a login for an MP, State Nodal Authority, or District Authority. They'll set their
          own password using the invite link below — nobody chooses a password on their behalf.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl shadow-subtle border border-gray-100">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">Total Accounts</span>
          <h3 className="font-headline font-bold text-2xl text-gray-900 mt-1">{users.length}</h3>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-subtle border border-emerald-100">
          <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Active</span>
          <h3 className="font-headline font-bold text-2xl text-emerald-700 mt-1">{activeCount}</h3>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-subtle border border-amber-100">
          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Invited</span>
          <h3 className="font-headline font-bold text-2xl text-amber-700 mt-1">{invitedCount}</h3>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-subtle border border-gray-100">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">Disabled</span>
          <h3 className="font-headline font-bold text-2xl text-gray-500 mt-1">{disabledCount}</h3>
        </div>
      </div>

      <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 rounded-xl border bg-surface p-6 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">Full name</label>
          <input
            required
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">Email</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">Role</label>
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value, scope_id: "" })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">
            {form.role === "mp" ? "MP" : form.role === "ministry" ? "Scope (n/a)" : "State / district name"}
          </label>
          {form.role === "mp" ? (
            <select
              required
              value={form.scope_id}
              onChange={(e) => setForm({ ...form, scope_id: e.target.value })}
              className="w-full rounded-lg border px-3 py-2 text-sm"
            >
              <option value="">Select an MP...</option>
              {mps.map((mp) => (
                <option key={mp.id} value={mp.id}>
                  {mp.name} ({mp.constituency_name}, {mp.state})
                </option>
              ))}
            </select>
          ) : form.role === "ministry" ? (
            <input disabled value="National (unrestricted)" className="w-full rounded-lg border bg-slate-50 px-3 py-2 text-sm text-gray-400" />
          ) : (
            <input
              required
              placeholder={form.role === "state_nodal" ? "e.g. Uttar Pradesh" : "e.g. Gorakhpur"}
              value={form.scope_id}
              onChange={(e) => setForm({ ...form, scope_id: e.target.value })}
              className="w-full rounded-lg border px-3 py-2 text-sm"
            />
          )}
        </div>

        {error && <p className="col-span-2 text-xs font-semibold text-rose-600">{error}</p>}

        <div className="col-span-2">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create account & generate invite"}
          </button>
        </div>
      </form>

      {lastInviteUrl && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm">
          <p className="font-bold text-emerald-800">Invite link (share this with the invitee):</p>
          <code className="mt-1 block break-all text-xs text-emerald-700">{lastInviteUrl}</code>
          <p className="mt-2 text-xs text-emerald-700">
            In production this would be emailed automatically. For now, copy and send it manually.
          </p>
        </div>
      )}

      <div className="rounded-xl border bg-surface">
        <div className="border-b px-4 py-2 text-xs font-bold text-gray-600">Accounts</div>
        <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-xs">
          <thead>
            <tr className="text-gray-500">
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Role</th>
              <th className="px-4 py-2">Scope</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = user.email === u.email;
              const statusColor =
                u.status === "active" ? "text-emerald-600" : u.status === "disabled" ? "text-rose-600" : "text-amber-600";
              const statusLabel = u.status === "active" ? "Active" : u.status === "disabled" ? "Disabled" : "Invited";
              return (
                <tr key={u.id} className="border-t">
                  <td className="px-4 py-2 font-semibold">{u.full_name}</td>
                  <td className="px-4 py-2 text-gray-500">{u.email}</td>
                  <td className="px-4 py-2">{u.role}</td>
                  <td className="px-4 py-2 text-gray-500">{u.scope_id ?? "—"}</td>
                  <td className="whitespace-nowrap px-4 py-2">
                    <div className="flex items-center gap-3">
                      {u.status !== "invited" && (
                        <button
                          type="button"
                          role="switch"
                          aria-checked={u.status === "active"}
                          title={isSelf ? "You can't deactivate your own account" : "Toggle account access"}
                          disabled={isSelf}
                          onClick={() => handleToggleActive(u.id)}
                          className={`relative inline-block h-5 w-9 shrink-0 rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                            u.status === "active" ? "bg-emerald-500" : "bg-gray-300"
                          }`}
                        >
                          <span
                            className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                              u.status === "active" ? "translate-x-4" : "translate-x-0"
                            }`}
                          />
                        </button>
                      )}
                      <span className={`font-bold ${statusColor}`}>{statusLabel}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    {u.status === "invited" && (
                      <button onClick={() => handleReinvite(u.id)} className="font-bold text-primary hover:underline">
                        Resend invite
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
