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
    return NextResponse.json(
      { success: false, error: "Semantic search failed", details: error.message },
      { status: 502 }
    );
  }
}
