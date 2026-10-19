import { handleApiRequest, HttpError } from "./game";
import type { Env } from "./types";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  try {
    const response = await handleApiRequest(request, env);
    const headers = new Headers(response.headers);
    for (const [name, value] of Object.entries(corsHeaders)) {
      headers.set(name, value);
    }
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (error) {
    if (error instanceof HttpError) {
      const headers = new Headers(corsHeaders);
      headers.set("Content-Type", "application/json; charset=utf-8");
      return new Response(JSON.stringify({ detail: error.message }), {
        status: error.status,
        headers,
      });
    }
    console.error("Queens API request failed.", error);
    return Response.json(
      { detail: "Error interno del servidor." },
      { status: 500, headers: corsHeaders },
    );
  }
};
