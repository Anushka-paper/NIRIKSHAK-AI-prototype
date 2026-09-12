import { NextResponse } from "next/server";
import { forwardAuthHeader } from "@/lib/serverAuth";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function POST(request: Request, context: { params: Promise<{ alertId: string }> }) {
  try {
    const { alertId } = await context.params;
    const res = await fetch(`${BACKEND_API}/alerts/${alertId}/resolve`, {
      method: "POST",
      headers: forwardAuthHeader(request),
    });
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
