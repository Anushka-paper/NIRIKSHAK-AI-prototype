import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "all";
  const state = searchParams.get("state") || "";
  const minScore = searchParams.get("min_score") || "0.70";
  const limit = searchParams.get("limit") || "50";
  const onlyAnomalies = searchParams.get("only_anomalies") || "true";

  let path = `/api/v1/anomalies?parliament=${parliament}&min_score=${minScore}&limit=${limit}&only_anomalies=${onlyAnomalies}`;
  if (state) {
    path += `&state=${encodeURIComponent(state)}`;
  }

  try {
    const data = await callMLService(path, { method: "GET" });
    return NextResponse.json({ success: true, data });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: "Failed to fetch anomalies", details: message },
      { status: 502 }
    );
  }
}
