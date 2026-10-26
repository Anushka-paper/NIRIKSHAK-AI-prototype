import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    
    if (!payload.query) {
      return NextResponse.json({ success: false, error: "Missing query parameter" }, { status: 400 });
    }

    const data = await callMLService("/api/nlp/check-duplicate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return NextResponse.json({ success: true, data });
  } catch (error: any) {
    // callMLService's error message embeds the upstream JSON body as raw
    // text (e.g. `ML Service returned status 503: {"detail":"..."}`) --
    // pull the actual detail out so the frontend can show the real reason
    // (e.g. "unavailable on this deployment") instead of that whole blob.
    const match = typeof error?.message === "string" ? error.message.match(/"detail"\s*:\s*"([^"]+)"/) : null;
    return NextResponse.json(
      { success: false, error: match ? match[1] : "Semantic search failed", details: error.message },
      { status: 502 }
    );
  }
}
