# Permanent deployment — Render

## One-click deploy

Open this link while logged into Render (GitHub sign-in works):

**https://render.com/deploy?repo=https://github.com/ailenskart/MellerGeo**

## Permanent URL

After deploy completes:

**https://meller-geo-intelligence.onrender.com**

## Required environment variables

In Render → `meller-geo-intelligence` → **Environment**:

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_MAPS_API_KEY` | Recommended | Live competitors, stores, Street View |
| `OPENAI_API_KEY` | Optional | AI chat + data verification |

Save changes — Render will redeploy automatically.

## Verify

```bash
curl https://meller-geo-intelligence.onrender.com/api/health
```

Expect `"status": "ok"` and `"google_maps_live": true` if the Maps key is set.
