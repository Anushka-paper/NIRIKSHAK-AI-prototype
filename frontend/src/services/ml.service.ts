/**
 * Server-Side ML Service Gateway.
 * Proxies requests between Next.js API route handlers and the Python FastAPI ML service.
 */

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://127.0.0.1:8000";

export async function callMLService<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${ML_SERVICE_URL}${endpoint}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error(`ML Service Error [${res.status}] ${url}:`, errorText);
      throw new Error(`ML Service returned status ${res.status}: ${errorText}`);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    console.error(`ML Service Connection Failed to ${url}:`, err);
    throw err;
  }
}

