"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChevronDown } from "lucide-react";
import { useAuth, roleLabel } from "@/lib/authContext";
import AlertBell from "@/components/AlertBell";

interface NavLink {
  name: string;
  href: string;
}

function NavDropdown({ label, items, pathname }: { label: string; items: NavLink[]; pathname: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const isActiveGroup = items.some((i) => i.href === pathname);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={`flex items-center gap-1 py-5 transition-colors ${
          isActiveGroup ? "text-primary border-b-2 border-primary" : "text-gray-600 hover:text-primary"
        }`}
      >
        {label}
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-50 min-w-[190px] rounded-xl border bg-white py-1.5 shadow-lg">
          {items.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setOpen(false)}
              className={`block px-4 py-2 text-sm font-semibold transition-colors ${
                pathname === item.href ? "text-primary bg-orange-50" : "text-gray-600 hover:bg-slate-50 hover:text-primary"
              }`}
            >
              {item.name}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  const authControl = user ? (
    <div className="flex items-center gap-3 text-xs">
      <AlertBell />
      <span className="hidden sm:block font-semibold text-gray-500">
        {user.fullName} &middot; <span className="text-primary">{roleLabel(user.role)}</span>
      </span>
      <button
        onClick={() => {
          logout();
          router.push("/login");
        }}
        className="rounded-lg border px-3 py-1.5 font-bold text-gray-600 hover:text-primary"
      >
        Log out
      </button>
    </div>
  ) : (
    <Link
      href="/login"
      className="rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-white"
    >
      Sign in
    </Link>
  );

  // Render custom header for landing/home page ("/")
  if (pathname === "/") {
    return (
      <header className="sticky top-0 z-50 w-full border-b border-transparent bg-background/90 backdrop-blur-md">
        <div className="container mx-auto flex h-20 items-center justify-between px-4 md:px-8">
          <div className="font-headline font-extrabold text-3xl text-primary tracking-tight">
            NIRIKSHAK<span className="text-secondary">AI</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#overview" className="text-sm font-bold text-gray-600 hover:text-primary transition-colors">
              View Overview
            </a>
            <Link href="/projects" className="text-sm font-bold text-gray-600 hover:text-primary transition-colors">
              Explore Projects &rarr;
            </Link>
            {authControl}
          </div>
        </div>
      </header>
    );
  }

  // Keep only the highest-traffic pages inline; everything else folds into
  // "Explore" so the bar doesn't run out of room once role-specific links
  // (Manage Accounts) get added on top of the base set.
  const primaryLinks: NavLink[] = [
    { name: "Overview", href: "/overview" },
    { name: "Compliance Audit", href: "/compliance" },
  ];

  const moreLinks: NavLink[] = [
    { name: "Browse States", href: "/states" },
    { name: "Projects", href: "/projects" },
    { name: "Anomalies", href: "/anomalies" },
    { name: "ML Dashboard", href: "/ml-dashboard" },
    ...(user?.role === "ministry" ? [{ name: "Manage Accounts", href: "/admin/users" }] : []),
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-surface/80 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center px-4 md:px-8">
        <Link href="/" className="font-headline font-bold text-2xl text-primary tracking-tight">
          NIRIKSHAK<span className="text-secondary">AI</span>
        </Link>
        <nav className="ml-8 hidden items-center gap-6 md:flex font-body font-semibold">
          {primaryLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`py-5 transition-colors ${
                  isActive ? "text-primary border-b-2 border-primary" : "text-gray-600 hover:text-primary"
                }`}
              >
                {link.name}
              </Link>
            );
          })}
          <NavDropdown label="Explore" items={moreLinks} pathname={pathname} />
        </nav>
        <div className="ml-auto">{authControl}</div>
      </div>
    </header>
  );
}
