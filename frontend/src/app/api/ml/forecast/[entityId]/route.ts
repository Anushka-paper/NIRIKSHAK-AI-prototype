import { NextRequest, NextResponse } from "next/server";

const ML_BASE = (process.env.ML_SERVICE_URL || process.env.ML_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ entityId: string }> }
) {
  try {
    const { entityId } = await params;
    const res = await fetch(`${ML_BASE}/api/forecast/${entityId}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json([], { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json([], { status: 503 });
  }
}
