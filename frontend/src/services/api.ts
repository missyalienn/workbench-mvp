import type { ApiResponse, ApiError } from "../types/api";

const DEMO_ENDPOINT_URL = "http://localhost:8000/api/run";
const TIMEOUT_MS = 60000;

export async function submitDemoQuery(
  query: string
): Promise<{ response?: ApiResponse; error?: ApiError }> {
  const requestAbortController = new AbortController();
  const requestTimeoutId = setTimeout(() => requestAbortController.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(DEMO_ENDPOINT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      signal: requestAbortController.signal,
    });

    clearTimeout(requestTimeoutId);

    if (response.status === 429) {
      return {
        error: {
          type: "rate_limit",
          message: "Rate limit exceeded. Please try again later.",
        },
      };
    }

    if (response.status === 422) {
      const body = await response.json().catch(() => null);
      return {
        error: {
          type: "server",
          message: body?.detail ?? "That doesn't look like a searchable topic. Try a question or subject you'd like to research.",
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

    const apiResponse: ApiResponse = await response.json();
    return { response: apiResponse };
  } catch (error) {
    clearTimeout(requestTimeoutId);

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
