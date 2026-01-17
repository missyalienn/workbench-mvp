import type { DemoResponse, ApiError } from "../types/api";

const API_URL = "http://localhost:8000/api/demo";
const TIMEOUT_MS = 60000;

export async function fetchDemo(
  query: string
): Promise<{ data?: DemoResponse; error?: ApiError }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 429) {
      return {
        error: {
          type: "rate_limit",
          message: "Rate limit exceeded. Please try again later.",
        },
      };
    }

    if (!response.ok) {
      return {
        error: {
          type: "server",
          message: `Server error: ${response.status} ${response.statusText}`,
        },
      };
    }

    const data: DemoResponse = await response.json();
    return { data };
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        return {
          error: {
            type: "timeout",
            message: "Request timed out. Please try again.",
          },
        };
      }
      if (error.message.includes("fetch")) {
        return {
          error: {
            type: "network",
            message: "Network error. Please check your connection.",
          },
        };
      }
    }

    return {
      error: {
        type: "network",
        message: "An unexpected error occurred.",
      },
    };
  }
}
