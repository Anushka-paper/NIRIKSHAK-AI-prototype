import { NextResponse } from "next/server";
import { forwardAuthHeader } from "@/lib/serverAuth";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function POST(request: Request, context: { params: Promise<{ findingId: string }> }) {
  try {
    const { findingId } = await context.params;
    const body = await request.json();
    const res = await fetch(`${BACKEND_API}/findings/${findingId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...forwardAuthHeader(request) },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ success: false, error: data.detail || "Failed to resolve finding" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
