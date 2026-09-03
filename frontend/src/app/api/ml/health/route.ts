import { NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export async function GET() {
  try {
    const health = await callMLService("/health", { method: "GET" });
    return NextResponse.json({
      success: true,
      gateway: "Next.js API Gateway",
      ml_service: health,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      {
        success: false,
        gateway: "Next.js API Gateway",
        error: "ML Service is currently unreachable",
        details: message,
      },
      { status: 503 }
    );
  }
}

