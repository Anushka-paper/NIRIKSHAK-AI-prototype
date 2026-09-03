import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const parliament = searchParams.get("parliament") || "all";

  try {
    const data = await callMLService(
      `/api/v1/overview/states/${encodeURIComponent(id)}/mps?parliament=${parliament}`,
      { method: "GET" }
    );
    return NextResponse.json({ success: true, data });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: `Failed to fetch MP performance for ${id}`, details: message },
      { status: 502 }
    );
  }
}
