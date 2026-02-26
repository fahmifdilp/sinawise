/**
 * MAGMA proxy for environments that cannot reach magma.esdm.go.id directly.
 * Route all requests under this worker to MAGMA origin.
 */
export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    const target = new URL(incoming.pathname + incoming.search, "https://magma.esdm.go.id");

    const upstream = await fetch(target.toString(), {
      method: request.method,
      headers: {
        "User-Agent": "sinabung-alert-mvp/1.0",
        Accept: request.headers.get("Accept") || "*/*",
      },
    });

    const headers = new Headers(upstream.headers);
    headers.set("access-control-allow-origin", "*");
    headers.set("cache-control", "public, max-age=60");

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers,
    });
  },
};
