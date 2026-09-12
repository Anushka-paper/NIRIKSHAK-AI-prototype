import Link from "next/link";
import { SearchX, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
          <SearchX className="h-6 w-6" />
        </div>
        <h2 className="font-headline text-xl font-bold text-slate-900">Page not found</h2>
        <p className="text-xs text-slate-500">
          The page you're looking for doesn't exist or may have moved.
        </p>
        <div className="flex justify-center pt-2">
          <Link
            href="/overview"
            className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white hover:bg-[var(--color-primary-hover)]"
          >
            <Home className="h-3.5 w-3.5" /> Back to Overview
          </Link>
        </div>
      </div>
    </div>
  );
}
