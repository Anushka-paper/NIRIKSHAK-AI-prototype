import { NextResponse } from "next/server";
import { forwardAuthHeader } from "@/lib/serverAuth";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function POST(request: Request, context: { params: Promise<{ userId: string }> }) {
  try {
    const { userId } = await context.params;
    const res = await fetch(`${BACKEND_API}/admin/users/${userId}/reinvite`, {
      method: "POST",
      headers: forwardAuthHeader(request),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ success: false, error: data.detail || "Failed to reinvite user" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
