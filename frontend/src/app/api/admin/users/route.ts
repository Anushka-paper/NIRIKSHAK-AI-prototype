import { NextResponse } from "next/server";
import { forwardAuthHeader } from "@/lib/serverAuth";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function GET(request: Request) {
  try {
    const res = await fetch(`${BACKEND_API}/admin/users`, { cache: "no-store", headers: forwardAuthHeader(request) });
    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json({ success: false, error: errorText }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_API}/admin/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...forwardAuthHeader(request) },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ success: false, error: data.detail || "Failed to create user" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
