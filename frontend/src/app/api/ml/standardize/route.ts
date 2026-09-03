import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "lok_sabha";

  try {
    const data = await callMLService(
      `/api/v1/standardization/reports?parliament=${parliament}`,
      { method: "GET" }
    );
    return NextResponse.json({ success: true, data });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: "Failed to fetch standardization reports", details: message },
      { status: 502 }
    );
  }
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "all";

  try {
    const data = await callMLService(
      `/api/v1/standardization/run?parliament=${parliament}`,
      { method: "POST" }
    );
    return NextResponse.json({ success: true, data });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: "Failed to trigger standardization", details: message },
      { status: 502 }
    );
  }
}

