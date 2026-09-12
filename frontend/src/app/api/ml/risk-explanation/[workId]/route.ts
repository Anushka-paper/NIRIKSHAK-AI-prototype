import { NextResponse } from "next/server";

const ML_SERVICE_URL = (process.env.ML_SERVICE_URL || process.env.BACKEND_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function GET(request: Request, context: { params: Promise<{ workId: string }> }) {
  try {
    const { workId } = await context.params;
    const res = await fetch(`${ML_SERVICE_URL}/api/works/${encodeURIComponent(workId)}/risk-explanation`, {
      cache: "no-store",
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ success: false, error: data.detail || "Failed to fetch risk explanation" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 502 });
  }
}
