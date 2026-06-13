"""
IR 222 -> FAH Water Balance — Vadose-Zone Uncertainty
Streamlit dashboard. Mirrors the verified HTML model cell-for-cell.

Run locally:   streamlit run app.py
Deploy free:   push this folder to GitHub, then deploy at https://share.streamlit.io
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# DATA — IR 222 Phase 2 Final Report, Tables 2-2 & 2-3 (Jacobs/Halcrow, 2022)
# All flows in m3/day. Years index 0..4 = 2021, 2025, 2030, 2035, 2040.
# --------------------------------------------------------------------------- #
YEARS = [2021, 2025, 2030, 2035, 2040]

SUPPLY = {
    "summer": {
        "Warsan STP":               [341484, 379523, 433084, 485813, 544965],
        "Jebel Ali STP":            [429204, 481604, 549573, 615731, 690702],
        "Private STP":              [0,      171920, 196183, 220823, 247710],
        "District Cooling Blowdown":[0,      9641,   39368,  63065,  91448],
    },
    "winter": {
        "Warsan STP":               [370816, 412121, 470284, 527542, 591775],
        "Jebel Ali STP":            [401875, 450940, 514580, 576526, 646724],
        "Private STP":              [0,      171920, 196183, 220823, 247710],
        "District Cooling Blowdown":[0,      6706,   21239,  32139,  43038],
    },
}
DEMAND = {
    "summer": {
        "Public Irrigation":      [331192, 382638, 424660, 467206, 512084],
        "Private Consumption":    [472368, 531601, 574785, 625113, 686141],
        "District Cooling":       [8859,   38566,  157470, 252259, 365793],
        "Private STP Irrigation": [0,      144773, 146455, 155907, 177486],
    },
    "winter": {
        "Public Irrigation":      [222114, 253498, 289318, 321109, 351348],
        "Private Consumption":    [312227, 356344, 406697, 451385, 493893],
        "District Cooling":       [7985,   26824,  84956,  128554, 172153],
        "Private STP Irrigation": [0,      130196, 148571, 166660, 186952],
    },
}
NRW = {
    "summer": {
        "Leakage":         [77069, 93293, 92968, 87501, 78741],
        "Creek Outfall":   [0, 0, 0, 0, 0],
        "Washout Lagoons": [0, 0, 0, 0, 0],
    },
    "winter": {
        "Leakage":         [77269, 93204, 91753, 85707, 76462],
        "Creek Outfall":   [95186, 0, 0, 0, 0],
        "Washout Lagoons": [57910, 0, 0, 0, 0],
    },
}
DEFAULTS = dict(fLeak=0.90, fDP=0.20, fLag=0.50,
                injSummer=0.0, injWinter=0.0, daysSummer=182, daysWinter=183)

# Plausible uncertainty ranges (FAH analysis — NOT IR 222 data).
RANGES = {
    "fDP":   dict(lo=0.05, hi=0.40, ex=0.20, vadose=True,
                  short="Irrigation deep-percolation (vadose zone)",
                  note="Governed by Van Genuchten retention of the fill / sand / Sabkha column — unmeasured in IR 222."),
    "fLeak": dict(lo=0.80, hi=0.95, ex=0.90, vadose=False,
                  short="Leakage reaching water table",
                  note="Buried leaks largely reach the table — a comparatively narrow band."),
    "fLag":  dict(lo=0.30, hi=0.70, ex=0.50, vadose=False,
                  short="Washout-lagoon infiltration",
                  note="Moderate; lagoons are only active in the 2021 base year."),
}

# Palette (matches the companion HTML / Excel deliverables)
C = dict(navy="#1F4E79", blue="#2E5496", grey="#595959", aquifer="#0E7C7B",
         consumed="#8C8C8C", discharged="#5B9BD5", banked="#7E57C2",
         shortage="#C0392B", surplus="#2E7D32")
NODE_COLOR = {
    "Warsan STP": "#2E5496", "Jebel Ali STP": "#3A66B0", "Private STP": "#5B82C9",
    "District Cooling Blowdown": "#86A5DC", "Public Irrigation": "#4C8C6B",
    "Private Consumption": "#3F7D9E", "District Cooling": "#9C8FB5",
    "Private STP Irrigation": "#6FA98C", "Leakage": "#C0762E",
    "Creek Outfall": "#5B9BD5", "Washout Lagoons": "#D49A4E",
    "Aquifer / Subsurface": C["aquifer"], "Consumed / Evapotranspired": C["consumed"],
    "Discharged to sea / creek": C["discharged"], "Banked (storage / ASR)": C["banked"],
    "Recycled Water Distributed": C["navy"],
    "Shortage (storage / alt supply)": C["shortage"], "ASR / injection": C["aquifer"],
}


# --------------------------------------------------------------------------- #
# MODEL — identical logic to the verified workbook / HTML
# --------------------------------------------------------------------------- #
def flows(season: str, yi: int, a: dict) -> dict:
    if season != "annual":
        return {
            "sup": {k: v[yi] for k, v in SUPPLY[season].items()},
            "dem": {k: v[yi] for k, v in DEMAND[season].items()},
            "nrw": {k: v[yi] for k, v in NRW[season].items()},
        }
    ds, dw = a["daysSummer"], a["daysWinter"]
    tot = ds + dw

    def blend(tbl):
        return {k: (tbl["summer"][k][yi] * ds + tbl["winter"][k][yi] * dw) / tot
                for k in tbl["summer"]}
    return {"sup": blend(SUPPLY), "dem": blend(DEMAND), "nrw": blend(NRW)}


def compute(season: str, yi: int, a: dict) -> dict:
    f = flows(season, yi, a)
    total_supply = sum(f["sup"].values())
    total_demand = sum(f["dem"].values())
    total_nrw = sum(f["nrw"].values())
    balance = total_supply - total_demand - total_nrw
    if season == "winter":
        inj = a["injWinter"]
    elif season == "summer":
        inj = a["injSummer"]
    else:
        inj = (a["injSummer"] * a["daysSummer"] + a["injWinter"] * a["daysWinter"]) \
              / (a["daysSummer"] + a["daysWinter"])
    r_leak = f["nrw"]["Leakage"] * a["fLeak"]
    applied = f["dem"]["Public Irrigation"] + f["dem"]["Private Consumption"] \
        + f["dem"]["Private STP Irrigation"]
    r_irr = applied * a["fDP"]
    r_lag = f["nrw"]["Washout Lagoons"] * a["fLag"]
    subsurface = r_leak + r_irr + r_lag + inj
    return dict(f=f, total_supply=total_supply, total_demand=total_demand,
                total_nrw=total_nrw, balance=balance, inj=inj, r_leak=r_leak,
                r_irr=r_irr, r_lag=r_lag, applied=applied, subsurface=subsurface,
                pct=subsurface / total_supply if total_supply else 0.0)


def annual(yi: int, a: dict) -> dict:
    s, w = compute("summer", yi, a), compute("winter", yi, a)
    ds, dw = a["daysSummer"], a["daysWinter"]
    return dict(supply=(s["total_supply"] * ds + w["total_supply"] * dw) / 1e6,
                sub=(s["subsurface"] * ds + w["subsurface"] * dw) / 1e6)


def subsurface_with(season, yi, a, overrides) -> float:
    return compute(season, yi, {**a, **overrides})["subsurface"]


def annual_sub_with(yi, a, overrides) -> float:
    return annual(yi, {**a, **overrides})["sub"]


def tornado_rows(season, yi, a):
    base = compute(season, yi, a)["subsurface"]
    rows = []
    for key, r in RANGES.items():
        lo_v = subsurface_with(season, yi, a, {key: r["lo"]})
        hi_v = subsurface_with(season, yi, a, {key: r["hi"]})
        rows.append(dict(key=key, short=r["short"], vadose=r["vadose"], note=r["note"],
                         low=min(lo_v, hi_v), high=max(lo_v, hi_v), swing=abs(hi_v - lo_v)))
    rows.sort(key=lambda x: x["swing"], reverse=True)
    return base, rows


def self_test() -> bool:
    a = dict(DEFAULTS)
    s21, w21 = compute("summer", 0, a), compute("winter", 0, a)
    s40, w40 = compute("summer", 4, a), compute("winter", 4, a)
    a21 = annual(0, a)
    ok = lambda x, y, t: abs(x - y) <= t
    return all([
        ok(s21["balance"], -118800, 1), ok(w21["balance"], 0, 1),
        ok(s21["r_leak"], 69362, 1), ok(s21["r_irr"], 160712, 1),
        ok(s21["subsurface"], 230074, 2), ok(w21["subsurface"], 205365, 2),
        ok(a21["supply"], 281.7, 0.2), ok(a21["sub"], 79.5, 0.2),
        ok(s40["balance"], -245420, 2), ok(w40["balance"], 248439, 2),
    ])


# --------------------------------------------------------------------------- #
# CHARTS
# --------------------------------------------------------------------------- #
def fmt(n) -> str:
    return f"{round(n):,}"


def build_sankey(c: dict, a: dict) -> go.Figure:
    labels, colors, idx = [], [], {}

    def node(label):
        if label not in idx:
            idx[label] = len(labels)
            labels.append(label)
            colors.append(NODE_COLOR.get(label, "#999"))
        return idx[label]

    src, tgt, val, lcol = [], [], [], []

    def link(a_lab, b_lab, value, color, alpha=0.40):
        if value <= 0:
            return
        src.append(node(a_lab)); tgt.append(node(b_lab)); val.append(value)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        lcol.append(f"rgba({r},{g},{b},{alpha})")

    hub = "Recycled Water Distributed"
    f = c["f"]
    # sources -> hub
    for k in SUPPLY["summer"]:
        link(k, hub, f["sup"].get(k, 0), NODE_COLOR[k])
    if c["balance"] < 0:
        link("Shortage (storage / alt supply)", hub, -c["balance"], C["shortage"])
    # hub -> uses
    for k in DEMAND["summer"]:
        link(hub, k, f["dem"].get(k, 0), NODE_COLOR[k])
    for k in NRW["summer"]:
        link(hub, k, f["nrw"].get(k, 0), NODE_COLOR[k])
    if c["balance"] > 0:
        link(hub, "Banked (storage / ASR)", c["balance"], C["banked"])
    # uses -> fate
    AQ, CO, DI = "Aquifer / Subsurface", "Consumed / Evapotranspired", "Discharged to sea / creek"
    for k in ("Public Irrigation", "Private Consumption", "Private STP Irrigation"):
        d = f["dem"].get(k, 0)
        link(k, AQ, d * a["fDP"], C["aquifer"], 0.85)
        link(k, CO, d * (1 - a["fDP"]), C["consumed"])
    link("District Cooling", CO, f["dem"].get("District Cooling", 0), C["consumed"])
    link("Leakage", AQ, c["r_leak"], C["aquifer"], 0.85)
    link("Leakage", CO, f["nrw"]["Leakage"] - c["r_leak"], C["consumed"])
    link("Creek Outfall", DI, f["nrw"]["Creek Outfall"], C["discharged"])
    link("Washout Lagoons", AQ, c["r_lag"], C["aquifer"], 0.85)
    link("Washout Lagoons", DI, f["nrw"]["Washout Lagoons"] - c["r_lag"], C["discharged"])
    if c["balance"] > 0:
        link("Banked (storage / ASR)", "Banked (storage / ASR) ", c["balance"], C["banked"])
    if c["inj"] > 0:
        link("ASR / injection", AQ, c["inj"], C["aquifer"], 0.85)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, color=colors, pad=16, thickness=18,
                  line=dict(color="rgba(0,0,0,0.15)", width=0.5),
                  hovertemplate="%{label}<br>%{value:,.0f} m³/day<extra></extra>"),
        link=dict(source=src, target=tgt, value=val, color=lcol,
                  hovertemplate="%{source.label} → %{target.label}"
                                "<br>%{value:,.0f} m³/day<extra></extra>"),
    ))
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10),
                      font=dict(family="Arial", size=13, color="#1c1c1c"))
    return fig


def build_tornado(season, yi, a) -> tuple[go.Figure, dict, list]:
    base, rows = tornado_rows(season, yi, a)
    rows_plot = list(reversed(rows))  # longest on top in a horizontal bar
    y = [r["short"] for r in rows_plot]
    base_x = [r["low"] for r in rows_plot]
    width = [r["high"] - r["low"] for r in rows_plot]
    bar_col = [C["aquifer"] if r["vadose"] else "#8FA8C8" for r in rows_plot]
    hover = [
        f"{r['short']}<br>subsurface {fmt(r['low'])} – {fmt(r['high'])} m³/day"
        f"<br>swing {fmt(r['swing'])} m³/day<br>{r['note']}"
        for r in rows_plot
    ]
    fig = go.Figure(go.Bar(
        y=y, x=width, base=base_x, orientation="h",
        marker=dict(color=bar_col, line=dict(color="#5d728f", width=0.5)),
        hovertext=hover, hoverinfo="text",
        text=[f"{fmt(r['low'])} – {fmt(r['high'])}" for r in rows_plot],
        textposition="outside", textfont=dict(size=11, color=C["grey"]),
    ))
    fig.add_vline(x=base, line_width=1.6, line_dash="dash", line_color=C["navy"],
                  annotation_text=f"expected {fmt(base)}", annotation_position="top",
                  annotation_font_color=C["navy"], annotation_font_size=11)
    fig.update_layout(height=300, margin=dict(l=10, r=80, t=30, b=10),
                      xaxis_title="Subsurface TSE reaching the ground (m³/day)",
                      font=dict(family="Arial", size=13, color="#1c1c1c"),
                      plot_bgcolor="white")
    fig.update_xaxes(gridcolor="#eef2f6", zeroline=False)
    return fig, dict(base=base), rows


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="IR 222 → FAH Water Balance", layout="wide",
                   page_icon="💧")

st.markdown(f"""
<style>
  .block-container {{padding-top: 1.6rem; max-width: 1300px;}}
  h1 {{color:{C['navy']}; font-size: 1.7rem;}}
  .fah-banner {{background:linear-gradient(90deg,#0E7C7B,#13a39f); color:#fff;
     border-radius:12px; padding:14px 18px; font-size:15px; margin:4px 0 14px;}}
  .fah-banner b {{font-size:18px;}}
  .hero {{border:1px solid {C['aquifer']}; background:#F0FAF9; border-radius:12px;
     padding:12px 16px;}}
  .hero .lbl {{font-size:12px; color:{C['grey']};}}
  .hero .val {{font-size:26px; font-weight:bold; color:{C['aquifer']};}}
  .hero .rng {{font-size:12px; color:{C['aquifer']}; font-weight:bold;}}
</style>
""", unsafe_allow_html=True)

st.title("IR 222 → FAH Water Balance — Vadose-Zone Uncertainty")
st.markdown(
    "How much recycled water (TSE) reaches Dubai's ground is **not a single number** — it hinges on "
    "the **vadose-zone deep-percolation fraction**, the least-measured term in the whole balance. "
    "This dashboard ranks which assumptions drive the uncertainty, so the dominant unknown is unmistakable."
)

# ---- sidebar controls ----
with st.sidebar:
    st.header("Scenario")
    yi = st.radio("Year", options=list(range(len(YEARS))),
                  format_func=lambda i: str(YEARS[i]), horizontal=True, index=0)
    season = st.radio("Season", options=["summer", "winter", "annual"],
                      format_func=str.capitalize, horizontal=True, index=0)
    st.divider()
    st.subheader("FAH assumptions")
    st.caption("Scenario levers — **not IR 222 data**. IR 222 contains no recharge, "
               "vadose-zone or subsurface accounting.")
    if st.button("Reset to defaults"):
        for k in ("fLeak", "fDP", "fLag", "injS", "injW"):
            st.session_state.pop(k, None)
        st.rerun()
    fDP = st.slider("Irrigation deep-percolation — VADOSE ZONE (%)", 0, 100,
                    int(DEFAULTS["fDP"] * 100), key="fDP") / 100
    fLeak = st.slider("Leakage reaching water table (%)", 0, 100,
                      int(DEFAULTS["fLeak"] * 100), key="fLeak",
                      help="Regime-dependent (Peche et al. 2026): in hydraulically *disconnected* "
                           "conditions (deep water table) the flux is pinned by pipe + colmation, "
                           "not by this fraction; in *connected* conditions (Dubai's rising-GW "
                           "regime) it couples nonlinearly to the water table.") / 100
    fLag = st.slider("Washout-lagoon infiltration (%)", 0, 100,
                     int(DEFAULTS["fLag"] * 100), key="fLag") / 100
    injS = st.number_input("ASR / injection — summer (m³/day)", min_value=0,
                           value=0, step=1000, key="injS")
    injW = st.number_input("ASR / injection — winter (m³/day)", min_value=0,
                           value=0, step=1000, key="injW")
    st.caption("Source: IR 222 Phase 2 Final Report (707883JA-P3-GE-REP-0001, "
               "Jul 2022), Tables 2-2 & 2-3 (Jacobs/Halcrow for Dubai Municipality).")

a = dict(DEFAULTS, fLeak=fLeak, fDP=fDP, fLag=fLag,
         injSummer=float(injS), injWinter=float(injW))

c = compute(season, yi, a)
an = annual(yi, a)

# ---- banner ----
a_lo = annual_sub_with(yi, a, {"fDP": RANGES["fDP"]["lo"], "fLeak": RANGES["fLeak"]["lo"],
                               "fLag": RANGES["fLag"]["lo"]})
a_hi = annual_sub_with(yi, a, {"fDP": RANGES["fDP"]["hi"], "fLeak": RANGES["fLeak"]["hi"],
                               "fLag": RANGES["fLag"]["hi"]})
st.markdown(
    f"<div class='fah-banner'>In {YEARS[yi]}, an estimated "
    f"<b>{an['sub']:.1f} Mm³ of recycled water reaches the ground each year</b> "
    f"(plausible <b>{a_lo:.1f}–{a_hi:.1f} Mm³</b>) — {an['sub']/an['supply']*100:.1f}% of all "
    f"TSE produced. <b>IR 222 accounts for none of it</b>, and the vadose term is the dominant unknown."
    "</div>", unsafe_allow_html=True)

# ---- KPI row ----
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total RW Supply", f"{fmt(c['total_supply'])}", "m³/day")
k2.metric("Total Demand", f"{fmt(c['total_demand'])}", "m³/day")
if c["balance"] < 0:
    k3.metric("Balance — SHORTAGE", f"−{fmt(-c['balance'])}", "met from storage / alt supply",
              delta_color="inverse")
else:
    k3.metric("Balance — SURPLUS", f"+{fmt(c['balance'])}", "banked to storage / ASR")
lo_all = subsurface_with(season, yi, a, {"fDP": RANGES["fDP"]["lo"], "fLeak": RANGES["fLeak"]["lo"],
                                         "fLag": RANGES["fLag"]["lo"]})
hi_all = subsurface_with(season, yi, a, {"fDP": RANGES["fDP"]["hi"], "fLeak": RANGES["fLeak"]["hi"],
                                         "fLag": RANGES["fLag"]["hi"]})
with k4:
    st.markdown(
        f"<div class='hero'><div class='lbl'>Subsurface TSE (FAH-revealed)</div>"
        f"<div class='val'>{fmt(c['subsurface'])}</div>"
        f"<div class='lbl'>{c['pct']*100:.1f}% of supply · m³/day</div>"
        f"<div class='rng'>plausible {fmt(lo_all)} – {fmt(hi_all)} m³/day</div></div>",
        unsafe_allow_html=True)

st.write("")

# ---- tornado (centrepiece) ----
st.subheader("Where the uncertainty lives — sensitivity of the subsurface estimate")
st.caption("Each bar spans the plausible low → high range of one FAH fraction (others held at "
           "their current values). A longer bar means more influence on how much TSE reaches the "
           "ground. The dashed line is the expected estimate.")
tfig, tinfo, rows = build_tornado(season, yi, a)
st.plotly_chart(tfig, use_container_width=True)

vad = next(r for r in rows if r["vadose"])
max_other = max((r["swing"] for r in rows if not r["vadose"]), default=0)
ratio = f"{vad['swing']/max_other:.1f}×" if max_other else "many ×"
st.markdown(
    f"The **vadose-zone deep-percolation fraction** alone moves the estimate across "
    f"**{fmt(vad['low'])} – {fmt(vad['high'])} m³/day** (a {fmt(vad['swing'])} m³/day swing) — about "
    f"**{ratio}** the largest of the other levers. This single unmeasured parameter dominates how "
    f"much TSE reaches the ground, which is why FAH resolves it with **HYDRUS-1D vadose columns over "
    f"Sabkha retention curves** rather than assuming a number.")
st.caption(
    "Independent support — [Peche et al. (2026, *Groundwater*)](https://doi.org/10.1111/gwat.70083) "
    "show numerically that the leaky-sewer → groundwater flux is **regime-dependent**: constant when "
    "the water table sits below a soil-specific disconnection depth (≈ 0.89 m sand / 1.77 m loamy "
    "sand / 4.00 m sandy loam), and nonlinearly coupled to the water table above it. Dubai's "
    "rising-GW regime is the latter — the leakage term here is therefore time-varying, not a fixed fraction.")

st.divider()

# ---- sankey + narrative ----
left, right = st.columns([1.5, 1])
with left:
    st.subheader("Water-balance flow — sources → distribution → uses → fate")
    st.plotly_chart(build_sankey(c, a), use_container_width=True)
with right:
    st.subheader("What IR 222 sees vs. what FAH reveals")
    st.markdown(f"**<span style='color:{C['navy']}'>What IR 222 sees</span>** — Supply, demand, "
                "billed consumption and non-revenue water. The balance closes at the meter and the "
                "pipe wall: leakage is *loss*, irrigation is *consumed*, surplus is *discharged or stored*.",
                unsafe_allow_html=True)
    st.markdown(f"**<span style='color:{C['aquifer']}'>What FAH reveals</span>** — Every one of those "
                "terms is a *located subsurface source*. Leakage becomes mapped recharge; irrigation "
                "becomes vadose-zone flux and Sabkha dissolution; ASR and lagoons become deliberate "
                "aquifer plumes — each with a path to specific assets and a settlement / liability "
                "consequence. Deep percolation is not a constant but a Richards'-equation process "
                "(HYDRUS-1D) over the fill / sand / Sabkha column — exactly the widest bar above.",
                unsafe_allow_html=True)
    st.info("The connection no one can see: the plan's biggest *losses* are the platform's primary evidence.")

# ---- self-test footer ----
if self_test():
    st.success("Model self-test: PASS — reproduces the 10 verified IR 222 / FAH check-values.", icon="✅")
else:
    st.error("Model self-test: FAIL — computed values diverge from the verified check-values.", icon="⚠️")
