import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="Dashboard Alokasi Minyak - Geragai/PHEJM/FSO",
                    layout="wide", page_icon="🛢️")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    geragai = pd.read_csv("data/cond_geragai.csv", parse_dates=["Tanggal"])
    phejm = pd.read_csv("data/cond_phejm.csv", parse_dates=["Tanggal"])
    crude = pd.read_csv("data/crude_geragai.csv", parse_dates=["Tanggal"])
    mix = pd.read_csv("data/cond_mix.csv", parse_dates=["Tanggal"])
    fso = pd.read_csv("data/fso.csv", parse_dates=["Tanggal"])
    rekap = pd.read_csv("data/rekap.csv", parse_dates=["Tanggal"])
    for df in (geragai, phejm, crude, mix, fso, rekap):
        df.columns = [c.strip() for c in df.columns]
    return geragai, phejm, crude, mix, fso, rekap

geragai, phejm, crude, mix, fso, rekap = load_data()

SOURCE_LABELS = {
    "geragai": "Condensate Geragai",
    "phejm": "Condensate PHEJM",
    "crude": "Crude Geragai",
    "mix": "Condensate Mix (T-101)",
}

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("🛢️ Filter")
min_date = min(geragai["Tanggal"].min(), phejm["Tanggal"].min(), crude["Tanggal"].min())
max_date = max(geragai["Tanggal"].max(), crude["Tanggal"].max(), fso["Tanggal"].max())

date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start_date, end_date = min_date, max_date

def flt(df):
    return df[(df["Tanggal"] >= start_date) & (df["Tanggal"] <= end_date)]

geragai_f, phejm_f, crude_f, mix_f, fso_f, rekap_f = (
    flt(geragai), flt(phejm), flt(crude), flt(mix), flt(fso), flt(rekap)
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: Condensate Geragai, Condensate PHEJM, Crude Geragai, "
    "Condensate Mix Tangki 770-T-101, FSO & Rekap Alokasi — periode Apr–Jun 2026."
)

# ---------------------------------------------------------------------------
# Header + KPI
# ---------------------------------------------------------------------------
st.title("🛢️ Dashboard Produksi & Alokasi Volume — Geragai / PHEJM / FSO")
st.caption(f"Periode ditampilkan: {start_date.date()} s/d {end_date.date()}")

total_fso = fso_f["Volume Total"].sum()
total_condensate_fso = fso_f["Condensate"].sum()
total_crude_fso = fso_f["Crude Geragai"].sum()
avg_alokasi_geragai = geragai_f["Alokasi Factor"].mean()
avg_alokasi_phejm = phejm_f["Alokasi Factor"].mean()
avg_disc_geragai = geragai_f["Diskrepansi"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Volume FSO (bbl)", f"{total_fso:,.0f}")
c2.metric("Total Condensate → FSO (bbl)", f"{total_condensate_fso:,.0f}")
c3.metric("Total Crude → FSO (bbl)", f"{total_crude_fso:,.0f}")
c4.metric("Rata² Alokasi Factor Geragai", f"{avg_alokasi_geragai:.4f}")
c5.metric("Rata² Diskrepansi Geragai", f"{avg_disc_geragai*100:.2f}%",
          delta=None, delta_color="inverse")

st.markdown("---")

tabs = st.tabs([
    "📈 Volume & Produksi", "🌡️ Kualitas (API/Suhu)", "💧 Losses & Shrinkage",
    "⚖️ Alokasi & Diskrepansi", "🚢 FSO & Ringkasan", "📋 Data Mentah"
])

# ---------------------------------------------------------------------------
# TAB 1 — Volume & Produksi
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Tren Volume Harian per Sumber")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["Net Volume"],
                              name="Condensate Geragai", mode="lines"))
    fig.add_trace(go.Scatter(x=phejm_f["Tanggal"], y=phejm_f["Net Volume"],
                              name="Condensate PHEJM", mode="lines"))
    fig.add_trace(go.Scatter(x=crude_f["Tanggal"], y=crude_f["Net Volume"],
                              name="Crude Geragai", mode="lines"))
    fig.add_trace(go.Scatter(x=mix_f["Tanggal"], y=mix_f["Total Net Vol"],
                              name="Condensate Mix (Total)", mode="lines"))
    fig.update_layout(height=450, xaxis_title="Tanggal", yaxis_title="Net Volume (bbl)",
                       legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Kontribusi Total Net Volume per Sumber")
        totals = pd.Series({
            "Condensate Geragai": geragai_f["Net Volume"].sum(),
            "Condensate PHEJM": phejm_f["Net Volume"].sum(),
            "Crude Geragai": crude_f["Net Volume"].sum(),
        })
        fig2 = px.pie(values=totals.values, names=totals.index, hole=0.45)
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.subheader("Shipping 1 vs Shipping 2 — Condensate Mix (T-101)")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=mix_f["Tanggal"], y=mix_f["Shipping 1 - Net Volume"],
                               name="Shipping 1"))
        fig3.add_trace(go.Bar(x=mix_f["Tanggal"], y=mix_f["Shipping 2 - Net Volume"],
                               name="Shipping 2"))
        fig3.update_layout(barmode="stack", height=380, yaxis_title="Net Volume (bbl)")
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Gross vs Net Volume (Geragai)")
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["Gross Vol"], name="Gross Vol"))
    fig4.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["Net Volume"], name="Net Volume"))
    fig4.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["GSV"], name="GSV"))
    fig4.update_layout(height=380, yaxis_title="Volume (bbl)")
    st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2 — Kualitas
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Tren API Gravity per Sumber")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["API"], name="Condensate Geragai"))
    fig.add_trace(go.Scatter(x=phejm_f["Tanggal"], y=phejm_f["API"], name="Condensate PHEJM"))
    fig.add_trace(go.Scatter(x=crude_f["Tanggal"], y=crude_f["API"], name="Crude Geragai"))
    fig.update_layout(height=420, yaxis_title="API Gravity (°API)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Temperature Harian")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["Temperature"], name="Geragai"))
        fig2.add_trace(go.Scatter(x=phejm_f["Tanggal"], y=phejm_f["Temperature"], name="PHEJM"))
        fig2.add_trace(go.Scatter(x=crude_f["Tanggal"], y=crude_f["Temperature"], name="Crude"))
        fig2.update_layout(height=380, yaxis_title="°C")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.subheader("Distribusi API Gravity")
        api_data = pd.concat([
            geragai_f[["API"]].assign(Sumber="Geragai"),
            phejm_f[["API"]].assign(Sumber="PHEJM"),
            crude_f[["API"]].assign(Sumber="Crude"),
        ])
        fig3 = px.box(api_data, x="Sumber", y="API", color="Sumber")
        fig3.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3 — Losses & Shrinkage
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Shrinkage & Losses Harian — Condensate Geragai")
    fig = go.Figure()
    for col in ["Emulsi", "Evaporasi", "Shrinkage Lv 1", "Shrinkage Lv 2"]:
        fig.add_trace(go.Bar(x=geragai_f["Tanggal"], y=geragai_f[col], name=col.strip()))
    fig.update_layout(barmode="stack", height=420, yaxis_title="bbl")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Losses per Sumber (kumulatif periode)")
        loss_cols_geragai = geragai_f[["Emulsi", "Evaporasi", "Shrinkage Lv 1", "Shrinkage Lv 2"]].sum()
        loss_cols_phejm = phejm_f[["Emulsi", "Evaporasi", "Shrinkage Lv 1", "Shrinkage Lv 2"]].sum()
        loss_df = pd.DataFrame({"Geragai": loss_cols_geragai.values,
                                 "PHEJM": loss_cols_phejm.values},
                                index=["Emulsi", "Evaporasi", "Shrinkage Lv 1", "Shrinkage Lv 2"])
        fig2 = px.bar(loss_df, barmode="group")
        fig2.update_layout(height=380, yaxis_title="bbl")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.subheader("% Loss terhadap Gross Volume")
        geragai_f2 = geragai_f.copy()
        geragai_f2["Total Loss"] = geragai_f2[["Emulsi", "Evaporasi", "Shrinkage Lv 1", "Shrinkage Lv 2"]].sum(axis=1)
        geragai_f2["% Loss"] = geragai_f2["Total Loss"] / geragai_f2["Gross Vol"] * 100
        fig3 = px.line(geragai_f2, x="Tanggal", y="% Loss")
        fig3.update_layout(height=380, yaxis_title="% Loss")
        st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4 — Alokasi & Diskrepansi (KPI paling kritikal)
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Alokasi Factor Harian (target ≈ 1.0000)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=geragai_f["Tanggal"], y=geragai_f["Alokasi Factor"], name="Geragai"))
    fig.add_trace(go.Scatter(x=phejm_f["Tanggal"], y=phejm_f["Alokasi Factor"], name="PHEJM"))
    fig.add_trace(go.Scatter(x=crude_f["Tanggal"], y=crude_f["Alokasi Factor"], name="Crude Geragai"))
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(height=420, yaxis_title="Alokasi Factor")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Diskrepansi Harian (%) — deviasi Receive vs Alokasi")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=geragai_f["Tanggal"], y=geragai_f["Diskrepansi"]*100, name="Geragai"))
    fig2.add_trace(go.Bar(x=phejm_f["Tanggal"], y=phejm_f["Diskrepansi"]*100, name="PHEJM"))
    fig2.add_hline(y=0, line_color="black")
    fig2.update_layout(barmode="group", height=420, yaxis_title="Diskrepansi (%)")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Alokasi Factor Gabungan (Rekap — Fluida Total)")
    if "Alokasi - Alokasi Factor - Fluida" in rekap_f.columns:
        fig3 = px.line(rekap_f, x="Tanggal", y="Alokasi - Alokasi Factor - Fluida")
        fig3.add_hline(y=1.0, line_dash="dash", line_color="gray")
        fig3.update_layout(height=380, yaxis_title="Alokasi Factor")
        st.plotly_chart(fig3, use_container_width=True)

    outlier_thresh = st.slider("Ambang Diskrepansi untuk flag outlier (%)", 1, 20, 5)
    flagged = geragai_f[geragai_f["Diskrepansi"].abs()*100 > outlier_thresh][["Tanggal", "Diskrepansi", "Alokasi Factor"]]
    st.markdown(f"**Hari dengan Diskrepansi Geragai > {outlier_thresh}%:**")
    st.dataframe(flagged, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 5 — FSO & Ringkasan
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Volume Diterima FSO Harian")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=fso_f["Tanggal"], y=fso_f["Condensate"], name="Condensate"))
    fig.add_trace(go.Bar(x=fso_f["Tanggal"], y=fso_f["Crude Geragai"], name="Crude Geragai"))
    fig.update_layout(barmode="stack", height=420, yaxis_title="bbl")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Volume FSO per Bulan")
        fso_month = fso_f.copy()
        fso_month["Bulan"] = fso_month["Tanggal"].dt.to_period("M").astype(str)
        monthly = fso_month.groupby("Bulan")[["Condensate", "Crude Geragai", "Volume Total"]].sum().reset_index()
        fig2 = px.bar(monthly, x="Bulan", y=["Condensate", "Crude Geragai"], barmode="stack")
        fig2.update_layout(height=380, yaxis_title="bbl")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.subheader("Ringkasan Volume Total")
        st.dataframe(monthly.style.format({"Condensate": "{:,.0f}", "Crude Geragai": "{:,.0f}", "Volume Total": "{:,.0f}"}),
                     use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 6 — Raw data
# ---------------------------------------------------------------------------
with tabs[5]:
    which = st.selectbox("Pilih sumber data", list(SOURCE_LABELS.values()) + ["FSO", "Rekap"])
    lookup = {v: k for k, v in SOURCE_LABELS.items()}
    if which == "FSO":
        st.dataframe(fso_f, use_container_width=True)
    elif which == "Rekap":
        st.dataframe(rekap_f, use_container_width=True)
    else:
        key = lookup[which]
        df_map = {"geragai": geragai_f, "phejm": phejm_f, "crude": crude_f, "mix": mix_f}
        st.dataframe(df_map[key], use_container_width=True)
