import { NextRequest, NextResponse } from "next/server";
import { callMLService } from "@/services/ml.service";

export interface PredictionPayload {
  work_id?: string;
  estimated_cost: number;
  days_since_sanction: number;
  current_status?: string;
  state?: string;
  category?: string;
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as PredictionPayload;

    if (!payload.estimated_cost || payload.days_since_sanction === undefined) {
      return NextResponse.json(
        {
          success: false,
          error: "estimated_cost and days_since_sanction are required fields",
        },
        { status: 400 }
      );
    }

    const prediction = await callMLService("/api/v1/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    return NextResponse.json({ success: true, data: prediction });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: "Prediction failed", details: message },
      { status: 502 }
    );
  }
}

