"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";

const DEMO_ACCOUNTS = [
  { label: "Member of Parliament", email: "mp@nirikshak.demo" },
  { label: "State Nodal Authority (UP)", email: "state.up@nirikshak.demo" },
  { label: "District Authority (Gorakhpur)", email: "district.gorakhpur@nirikshak.demo" },
  { label: "Ministry", email: "ministry@nirikshak.demo" },
];

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/overview");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md py-12">
      <h1 className="font-headline text-2xl font-extrabold text-primary mb-1">Sign in</h1>
      <p className="text-sm text-gray-500 mb-6">
        Access your role-scoped MPLADS compliance dashboard.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border bg-surface p-6">
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="you@nirikshak.demo"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600 mb-1">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-sm"
          />
        </div>

        {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-primary py-2 text-sm font-bold text-white disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div className="mt-6 rounded-xl border bg-slate-50 p-4">
        <p className="text-xs font-bold text-gray-600 mb-2">Demo accounts (password: demo1234)</p>
        <ul className="space-y-1">
          {DEMO_ACCOUNTS.map((acc) => (
            <li key={acc.email}>
              <button
                type="button"
                onClick={() => setEmail(acc.email)}
                className="text-xs text-primary hover:underline"
              >
                {acc.label} — {acc.email}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
