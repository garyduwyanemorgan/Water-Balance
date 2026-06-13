# IR 222 → FAH Water Balance

Interactive dashboard showing how much recycled water (TSE) reaches Dubai's ground —
and why the **vadose-zone deep-percolation fraction** dominates the uncertainty in that
estimate. Built on the Forensic Asset Hydrogeology (FAH) water-balance model; mirrors
the verified workbook `IR222_FAH_Water_Balance.xlsx` and passes the same 10 check-values.

Independent support for the framing: Peche et al. (2026, *Groundwater*) —
[doi:10.1111/gwat.70083](https://doi.org/10.1111/gwat.70083) — show numerically that
leaky-sewer → groundwater flux is regime-dependent (constant below soil-specific
disconnection depths of ~0.89 m sand / 1.77 m loamy sand / 4.00 m sandy loam,
nonlinearly coupled to the water table above), framing why Dubai's rising-GW regime
makes the leakage term time-varying rather than a fixed fraction.

## Two deployments, one repo

| Version | File(s) | Host | URL pattern | Trade-off |
|---|---|---|---|---|
| **Static HTML** | `docs/index.html` | GitHub Pages (free) | `https://<user>.github.io/Water-Balance/` | Instant load, always-on, no backend. Self-contained SVG/JS. |
| **Streamlit dashboard** | `app.py` + `requirements.txt` + `render.yaml` | Render (free) | `https://<service>.onrender.com` (or your custom domain) | Sidebar controls, Plotly Sankey, polished — but free tier sleeps after 15 min idle (~30 s cold start). |

Both renders compute identical numbers from the same data — verified by an in-app
self-test against 10 IR 222 check-values.

## Run the Streamlit version locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501.

## Deploy the static HTML on GitHub Pages

In this repo: **Settings → Pages → Source: Deploy from a branch → Branch: `main` /
`/docs` folder → Save**. After ~30 s the page is live at
`https://<your-github-user>.github.io/Water-Balance/`.

## Deploy the Streamlit app on Render

`render.yaml` configures the service automatically:
1. At [render.com](https://render.com) → **New + → Blueprint** → connect this repo.
2. Render reads `render.yaml` and provisions a free web service.
3. After build (~3 min) the app is live at the `*.onrender.com` URL.

### Attach a custom domain

In Render: **Settings → Custom Domains → Add** → enter the subdomain
(e.g. `fahinputs.example.com`). Render shows a target CNAME — add it as a CNAME record
in your DNS provider (GoDaddy/Cloudflare/etc.). Render auto-issues a Let's Encrypt
TLS cert once DNS resolves.

## What the dashboard shows

- **KPI cards** — supply, demand, surplus/shortage, and the hero **subsurface TSE**
  with a plausible low–high range.
- **Sensitivity tornado** — ranks each FAH fraction by how far its plausible range
  swings the subsurface estimate. The vadose-zone fraction lands on top by a wide
  margin (~24× the next-largest lever).
- **Sankey flow** — sources → distribution → uses & losses → fate, with the aquifer
  flow highlighted in teal.
- **Year / season / assumption controls** recompute everything live.

All numbers are FAH analysis layered on IR 222 surface data; the subsurface layer and
the uncertainty ranges are clearly labelled as inference, not IR 222 data.

## Source

IR 222 Phase 2 Final Report (707883JA-P3-GE-REP-0001, Jul 2022), Tables 2-2 & 2-3
(Jacobs/Halcrow for Dubai Municipality). Surface balance reconciles to IR 222's
stated 2021 shortage of −118,800 m³/day and annual ~284 Mm³/yr produced.
