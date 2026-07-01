# Deploy to Vercel

## Permanent URL

After import: **https://meller-geo-intelligence.vercel.app**

(Vercel may assign a variant like `meller-geo-intelligence-ailenskart.vercel.app` — both are permanent.)

## Steps

1. Open **https://vercel.com/new**
2. Connect GitHub → select **ailenskart/MellerGeo**
3. Framework preset: **Other** (uses `vercel.json`)
4. Click **Deploy** (first build ~3–5 min)
5. **Settings → Environment Variables**:
   - `GOOGLE_MAPS_API_KEY`
   - `OPENAI_API_KEY` (optional)
6. **Deployments → Redeploy** after adding env vars

## Verify

```bash
curl https://YOUR-PROJECT.vercel.app/api/health
```

## Architecture on Vercel

- **Frontend** — static React build in `public/` (CDN)
- **API** — FastAPI serverless function at `api/index.py`
- **ML model** — bundled with the Python function (`backend/models/`)

## Limits

| Plan | API timeout | Notes |
|------|-------------|-------|
| Hobby (free) | 10 seconds | Fast endpoints only; intelligence may timeout |
| Pro | 60 seconds | Full AI verification + Google intelligence |

## CLI deploy (optional)

```bash
npm i -g vercel
vercel login
vercel --prod
```

Set env vars in the Vercel dashboard or via `vercel env add`.
