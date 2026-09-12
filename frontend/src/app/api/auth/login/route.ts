import { NextResponse } from "next/server";

const BACKEND_API = process.env.BACKEND_API_URL || process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({ detail: "Login failed" }));
      return NextResponse.json({ error: errorBody.detail || "Login failed" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Login service unavailable" }, { status: 502 });
  }
}
