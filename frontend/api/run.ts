/**
 * Vercel server-side proxy for Workbench API requests.
 *
 * Usage:
 * Send a `POST /api/run` request from the browser. This function forwards the
 * request to Lambda and injects the server-side proxy token header.
 */
const PROXY_TOKEN_HEADER = "X-Workbench-Proxy-Token";

function requiredEnv(name: "LAMBDA_URL" | "PROXY_TOKEN"): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export async function POST(request: Request): Promise<Response> {
  let lambdaUrl: string;
  let proxyToken: string;

  try {
    lambdaUrl = requiredEnv("LAMBDA_URL");
    proxyToken = requiredEnv("PROXY_TOKEN");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Missing proxy configuration.";
    return new Response(message, { status: 500 });
  }

  const requestBody = await request.text();
  const upstreamHeaders = new Headers();
  upstreamHeaders.set(
    "Content-Type",
    request.headers.get("content-type") ?? "application/json",
  );
  upstreamHeaders.set(PROXY_TOKEN_HEADER, proxyToken);

  const acceptHeader = request.headers.get("accept");
  if (acceptHeader) {
    upstreamHeaders.set("Accept", acceptHeader);
  }

  const upstreamResponse = await fetch(lambdaUrl, {
    method: "POST",
    headers: upstreamHeaders,
    body: requestBody,
  });

  const responseHeaders = new Headers();
  const contentType = upstreamResponse.headers.get("content-type");
  if (contentType) {
    responseHeaders.set("Content-Type", contentType);
  }

  const responseBody = await upstreamResponse.text();
  return new Response(responseBody, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}
