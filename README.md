# IR 222 → FAH Water Balance (Streamlit)

Interactive dashboard showing how much recycled water (TSE) reaches Dubai's ground —
and why the **vadose-zone deep-percolation fraction** dominates the uncertainty in that
estimate. Built on the Forensic Asset Hydrogeology (FAH) water-balance model; mirrors the
verified workbook `IR222_FAH_Water_Balance.xlsx` and passes the same 10 check-values.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501.

## Deploy free (public URL for LinkedIn)

1. Create a new **public GitHub repo** and push the contents of this `fah-streamlit/` folder
   (`app.py`, `requirements.txt`, `README.md`) to its root.
2. Go to **https://share.streamlit.io**, sign in with GitHub, click **New app**.
3. Select your repo, branch `main`, main file `app.py`, then **Deploy**.
4. You get a permanent URL like `https://<your-app>.streamlit.app` — paste that into your
   LinkedIn post.

> First deploy takes ~1–2 minutes while it installs dependencies. Pushes to `main`
> auto-redeploy.

## What it shows

- **KPI cards** — supply, demand, surplus/shortage, and the hero **subsurface TSE** with a
  plausible low–high range.
- **Sensitivity tornado** — ranks each FAH fraction by how far its plausible range swings the
  subsurface estimate. The vadose-zone fraction lands on top, by a wide margin.
- **Sankey flow** — sources → distribution → uses & losses → fate, with the aquifer flow
  highlighted in teal.
- **Year / season / assumption controls** in the sidebar recompute everything live.

All numbers are FAH analysis layered on IR 222 surface data; the subsurface layer and the
uncertainty ranges are clearly labelled as inference, not IR 222 data.
