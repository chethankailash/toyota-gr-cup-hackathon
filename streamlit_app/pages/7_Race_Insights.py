# streamlit_app/pages/7_Race_Insights.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import DataLoader
from utils.track_meta import TrackMeta
from utils.theme import apply_toyota_theme

apply_toyota_theme()

# ---------------------------------------------------------
# 🎨 Toyota GR Theme Colors
# ---------------------------------------------------------
PRIMARY_RED = "#EB0A1E"
DARK_GRAY = "#58595B"
BLACK = "#000000"
WHITE = "#FFFFFF"


# ---------------------------------------------------------
# UI COMPONENTS (Reusable)
# ---------------------------------------------------------
def section_header(text):
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;margin-top:1.4rem;margin-bottom:0.7rem;">
            <div style="
                width:6px;
                height:22px;
                background:{PRIMARY_RED};
                border-radius:4px;
                margin-right:10px;">
            </div>
            <div style="font-size:1.25rem;font-weight:700;color:{BLACK};">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value):
    st.markdown(
        f"""
        <div style="
            border-left:4px solid {PRIMARY_RED};
            padding:0.6rem 1rem;
            background:#fafafa;
            border-radius:6px;
            margin-bottom:0.4rem;">
            <div style="font-size:0.85rem;color:{DARK_GRAY};font-weight:600;">
                {title}
            </div>
            <div style="font-size:1.25rem;font-weight:700;color:{BLACK};margin-top:4px;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.set_page_config(layout="wide")

st.markdown(
    f"""
    <h1 style="color:{PRIMARY_RED}; font-weight:800; margin-bottom:0;">
        Toyota GR – Race Insights & Driver Comparison
    </h1>
    <p style="color:{DARK_GRAY}; margin-top:4px; font-size:0.95rem;">
        Compare drivers on consistency, cumulative race time, and sector performance.
    </p>
    <hr style="border:1px solid {DARK_GRAY}; margin-top:-2px; margin-bottom:1.2rem;">
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def build_lap_time_seconds(df):
    lap = pd.to_numeric(df.get("lap_time_s", np.nan), errors="coerce")
    lap = lap.where(lap < 1000, lap / 1000)  # ms → s

    # fallback to sector sum
    for c in ["s1_seconds", "s2_seconds", "s3_seconds"]:
        if c not in df.columns:
            df[c] = np.nan

    sec_sum = (
        pd.to_numeric(df["s1_seconds"], errors="coerce").fillna(0)
        + pd.to_numeric(df["s2_seconds"], errors="coerce").fillna(0)
        + pd.to_numeric(df["s3_seconds"], errors="coerce").fillna(0)
    )

    lap = lap.where(lap.notna(), sec_sum)

    # final fill
    if lap.isna().any():
        lap = lap.fillna(lap.dropna().median() if len(lap.dropna()) else 120.0)

    return lap


def build_car_lap_df(sectors_df, track, car_number):
    df = sectors_df[sectors_df["track"] == track].copy()
    if df.empty:
        return pd.DataFrame()

    df = df[df["vehicle_number"] == car_number].copy()
    if df.empty:
        return pd.DataFrame()

    # Lap number
    if "lap" in df.columns:
        df["lap_number"] = pd.to_numeric(df["lap"], errors="coerce")
    elif "lap_number" in df.columns:
        df["lap_number"] = pd.to_numeric(df["lap_number"], errors="coerce")
    else:
        df["lap_number"] = np.arange(1, len(df) + 1)

    df = df.dropna(subset=["lap_number"])
    df["lap_number"] = df["lap_number"].astype(int)

    # Lap time
    df["lap_time_s"] = build_lap_time_seconds(df)

    # Sectors numeric
    for c in ["s1_seconds", "s2_seconds", "s3_seconds"]:
        df[c] = pd.to_numeric(df.get(c, np.nan), errors="coerce")

    # Keep only useful columns
    keep = ["lap_number", "lap_time_s", "s1_seconds", "s2_seconds", "s3_seconds", "vehicle_number"]
    for extra in ["driver_name", "team", "class", "group"]:
        if extra in df.columns:
            keep.append(extra)

    df = df[keep].sort_values("lap_number")
    df = df[(df["lap_time_s"] > 20) & (df["lap_time_s"] < 300)]

    return df


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())

sectors = data["sectors"]
if sectors.empty:
    st.error("No lap/sector data found.")
    st.stop()

if "track" not in sectors.columns or "vehicle_number" not in sectors.columns:
    st.error("Sector data missing columns.")
    st.stop()


# ---------------------------------------------------------
# Track selection
# ---------------------------------------------------------
track = st.selectbox("Select Track", meta.get_tracks())
track_sec = sectors[sectors["track"] == track].copy()

if track_sec.empty:
    st.error(f"No data for track {track}.")
    st.stop()


# ---------------------------------------------------------
# Car + Driver selection
# ---------------------------------------------------------
car_meta = (
    track_sec.groupby("vehicle_number")
    .agg(
        laps=("lap", "count") if "lap" in track_sec.columns else ("lap_time_s", "count"),
        driver_name=("driver_name", lambda x: x.dropna().iloc[0] if len(x.dropna()) else ""),
        team=("team", lambda x: x.dropna().iloc[0] if len(x.dropna()) else "")
    )
    .reset_index()
)

car_meta = car_meta.sort_values("vehicle_number")

def build_label(row):
    label = f"#{int(row['vehicle_number'])}"
    if row["driver_name"]:
        label += f" – {row['driver_name']}"
    return label

car_meta["label"] = car_meta.apply(build_label, axis=1)

options = car_meta["label"].tolist()
default = options[:2] if len(options) >= 2 else options

selected_labels = st.multiselect(
    "Select up to two cars for comparison",
    options,
    default=default,
    max_selections=2,
)

if not selected_labels:
    st.info("Select at least one car to begin.")
    st.stop()

selected_meta = car_meta[car_meta["label"].isin(selected_labels)]
selected_cars = selected_meta["vehicle_number"].tolist()


# ---------------------------------------------------------
# Build per-car lap tables
# ---------------------------------------------------------
car_dfs = {}
for car in selected_cars:
    df_car = build_car_lap_df(sectors, track, car)
    if not df_car.empty:
        car_dfs[car] = df_car

if not car_dfs:
    st.error("No usable lap data for selected cars.")
    st.stop()


# ---------------------------------------------------------
# SECTION 1 — Summary Metrics
# ---------------------------------------------------------
section_header(f"Race Summary — {track}")

rows = []
for car, dfc in car_dfs.items():
    best = dfc["lap_time_s"].min()
    avg = dfc["lap_time_s"].mean()
    med = dfc["lap_time_s"].median()
    laps = dfc["lap_number"].max()

    driver = dfc.get("driver_name", pd.Series([""])).iloc[0]
    team = dfc.get("team", pd.Series([""])).iloc[0]

    rows.append({
        "Car #": int(car),
        "Driver": driver,
        "Team": team,
        "Laps": laps,
        "Best Lap (s)": round(best, 3),
        "Avg Lap (s)": round(avg, 3),
        "Median Lap (s)": round(med, 3),
    })

summary_df = pd.DataFrame(rows)
st.dataframe(summary_df, use_container_width=True)


# ---------------------------------------------------------
# SECTION 2 — Lap Time Trend
# ---------------------------------------------------------
section_header("Lap Time Trend Comparison")

trend = []
for car, dfc in car_dfs.items():
    label = f"#{int(car)}"
    if "driver_name" in dfc.columns and dfc["driver_name"].dropna().size > 0:
        label += f" – {dfc['driver_name'].dropna().iloc[0]}"
    tmp = dfc[["lap_number", "lap_time_s"]].copy()
    tmp["car_label"] = label
    trend.append(tmp)

trend_df = pd.concat(trend, ignore_index=True)

fig_trend = px.line(
    trend_df,
    x="lap_number",
    y="lap_time_s",
    color="car_label",
    markers=True,
    color_discrete_sequence=[PRIMARY_RED, DARK_GRAY, BLACK],
)
fig_trend.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_trend, use_container_width=True)


# ---------------------------------------------------------
# SECTION 3 — Cumulative Race Time
# ---------------------------------------------------------
section_header("Cumulative Race Time")

cum_list = []
for car, dfc in car_dfs.items():
    dfc = dfc.sort_values("lap_number")
    dfc["cum_time_s"] = dfc["lap_time_s"].cumsum()
    label = f"#{int(car)}"
    if "driver_name" in dfc.columns and dfc["driver_name"].dropna().size > 0:
        label += f" – {dfc['driver_name'].dropna().iloc[0]}"
    tmp = dfc[["lap_number", "cum_time_s"]].copy()
    tmp["car_label"] = label
    cum_list.append(tmp)

cum_df = pd.concat(cum_list, ignore_index=True)

fig_cum = px.line(
    cum_df,
    x="lap_number",
    y="cum_time_s",
    color="car_label",
    color_discrete_sequence=[PRIMARY_RED, DARK_GRAY, BLACK],
)
fig_cum.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_cum, use_container_width=True)


# ---------------------------------------------------------
# SECTION 4 — Lap Time Distribution
# ---------------------------------------------------------
section_header("Lap Time Distribution")

box_list = []
for car, dfc in car_dfs.items():
    label = f"#{int(car)}"
    if "driver_name" in dfc.columns and dfc["driver_name"].dropna().size > 0:
        label += f" – {dfc['driver_name'].dropna().iloc[0]}"
    tmp = dfc[["lap_time_s"]].copy()
    tmp["car_label"] = label
    box_list.append(tmp)

box_df = pd.concat(box_list, ignore_index=True)

fig_box = px.box(
    box_df,
    x="car_label",
    y="lap_time_s",
    points="all",
    color_discrete_sequence=[PRIMARY_RED, DARK_GRAY, BLACK],
)
fig_box.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_box, use_container_width=True)


# ---------------------------------------------------------
# SECTION 5 — Sector Averages
# ---------------------------------------------------------
section_header("Sector Average Comparison")

sector_rows = []
for car, dfc in car_dfs.items():
    if not {"s1_seconds", "s2_seconds", "s3_seconds"}.issubset(dfc.columns):
        continue

    lbl = f"#{int(car)}"
    if "driver_name" in dfc.columns and dfc["driver_name"].dropna().size > 0:
        lbl += f" – {dfc['driver_name'].dropna().iloc[0]}"

    sector_rows.extend([
        {"car_label": lbl, "sector": "S1", "time_s": dfc["s1_seconds"].mean()},
        {"car_label": lbl, "sector": "S2", "time_s": dfc["s2_seconds"].mean()},
        {"car_label": lbl, "sector": "S3", "time_s": dfc["s3_seconds"].mean()},
    ])

if sector_rows:
    sec_df = pd.DataFrame(sector_rows)
    sec_df["time_s"] = sec_df["time_s"].round(3)

    fig_sector = px.bar(
        sec_df,
        x="sector",
        y="time_s",
        color="car_label",
        barmode="group",
        color_discrete_sequence=[PRIMARY_RED, DARK_GRAY, BLACK],
    )
    fig_sector.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

    st.plotly_chart(fig_sector, use_container_width=True)

    st.dataframe(
        sec_df.pivot(index="car_label", columns="sector", values="time_s")
        .reset_index(),
        use_container_width=True,
    )
else:
    st.info("Sector timing incomplete — skipping this section.")


# ---------------------------------------------------------
# SECTION 6 — Raw Data
# ---------------------------------------------------------
section_header("Raw Per-Lap Data")

with st.expander("View Raw Lap Tables"):
    for car, dfc in car_dfs.items():
        st.subheader(f"Car #{int(car)}")
        cols = ["lap_number", "lap_time_s", "s1_seconds", "s2_seconds", "s3_seconds", "driver_name", "team"]
        cols = [c for c in cols if c in dfc.columns]
        st.dataframe(dfc[cols].reset_index(drop=True))
        st.markdown("---")
