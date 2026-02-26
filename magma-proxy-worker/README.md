Cloudflare Worker MAGMA Proxy

Purpose
- Forward requests to `https://magma.esdm.go.id` so Railway backend can read MAGMA through Cloudflare edge.

Deploy
1. Install Wrangler:
   - `npm install -g wrangler`
2. Login:
   - `wrangler login`
3. Deploy from this folder:
   - `cd magma-proxy-worker`
   - `wrangler deploy`
4. Test:
   - `curl https://<your-worker-domain>/v1/gunung-api/tingkat-aktivitas`

Railway setup
1. Set variable:
   - `MAGMA_TINGKAT_URL=https://<your-worker-domain>/v1/gunung-api/tingkat-aktivitas`
2. Redeploy Railway service.

Notes
- This worker currently proxies GET and forwards minimal headers.
- CORS is open (`*`) for easier app consumption.
