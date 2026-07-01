# Deploy to Railway

## Permanent URL

After deploy: **`https://meller-geo-intelligence-production.up.railway.app`**

(Railway assigns a unique subdomain — you can also add a custom domain like `geo.mellerbrand.com`.)

## Why Railway for MELLER Geo

- **Full Docker** — same image as local/production, no serverless limits
- **No 10s timeout** — AI intelligence + Google verification work fully
- **ML model stays loaded** — faster responses after first request
- **Auto-deploy** on every push to `main`

## Deploy (2 minutes)

1. Open **https://railway.app/new**
2. Sign in with **GitHub**
3. Choose **Deploy from GitHub repo** → select **ailenskart/MellerGeo**
4. Railway auto-detects the `Dockerfile` and `railway.toml`
5. Go to your service → **Variables** and add:

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_MAPS_API_KEY` | Yes | Live competitors, stores, Street View |
| `OPENAI_API_KEY` | Recommended | AI chat + verification |
| `PORT` | Auto-set | Railway injects this — do not override |

6. **Settings → Networking → Generate Domain** to get your public HTTPS URL

First build takes ~5–8 minutes (Docker + npm + Python deps).

## Verify

```bash
curl https://YOUR-APP.up.railway.app/api/health
```

Expect `"status": "ok"` and `"google_maps_live": true`.

## CLI deploy (optional)

```bash
npm i -g @railway/cli
railway login
railway link
railway up
railway domain
```

## Pricing

- **Trial**: $5 one-time credit for new accounts
- **Hobby**: ~$5/month usage-based — enough for internal expansion tooling
- No cold-start sleep like Render free tier
