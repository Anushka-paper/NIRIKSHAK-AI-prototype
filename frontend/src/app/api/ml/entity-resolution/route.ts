import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "lok_sabha";
  const type = searchParams.get("type") || "matches";
  const limit = searchParams.get("limit") || "100";
  const offset = searchParams.get("offset") || "0";

  const endpoint =
    type === "review-queue"
      ? `/api/v1/entities/review-queue?parliament=${parliament}&limit=${limit}&offset=${offset}`
      : `/api/v1/entities/matches?parliament=${parliament}&limit=${limit}&offset=${offset}`;

  try {
    const data = await callMLService(endpoint, { method: "GET" });
    return NextResponse.json({ success: true, data });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: "Failed to fetch entity resolution data", details: message },
      { status: 502 }
    );
  }
}

