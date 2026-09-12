import { NextResponse } from "next/server";
import { forwardAuthHeader } from "@/lib/serverAuth";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function GET(request: Request) {
  try {
    const res = await fetch(`${BACKEND_API}/review-queue`, { cache: "no-store", headers: forwardAuthHeader(request) });
    if (!res.ok) {
      return NextResponse.json({ success: false, error: "Failed to fetch review queue" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

