import { NextRequest, NextResponse } from "next/server";

const ML_BASE = (process.env.ML_SERVICE_URL || process.env.ML_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "all";
  try {
    const res = await fetch(`${ML_BASE}/api/anomalies/states?parliament=${parliament}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ data: [] }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ data: [] }, { status: 503 });
  }
}
