"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="font-headline text-xl font-bold text-slate-900">Something went wrong</h2>
        <p className="text-xs text-slate-500">
          This page hit an unexpected error. You can try again, or head back to a working page.
        </p>
        {process.env.NODE_ENV === "development" && (
          <p className="rounded-lg bg-slate-50 p-2 text-left text-[11px] text-slate-500 break-words">
            {error.message}
          </p>
        )}
        <div className="flex justify-center gap-2 pt-2">
          <button
            onClick={reset}
            className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white hover:bg-[var(--color-primary-hover)]"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </button>
          <Link
            href="/overview"
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50"
          >
            <Home className="h-3.5 w-3.5" /> Back to Overview
          </Link>
        </div>
      </div>
    </div>
  );
}
