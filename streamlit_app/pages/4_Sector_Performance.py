# streamlit_app/pages/4_Sector_Performance.py

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
# Shared UI Components
# ---------------------------------------------------------
def section_header(text, color=BLACK):
    """Standard Toyota-style section header with left red bar."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;margin-top:1.5rem;margin-bottom:0.6rem;">
            <div style="width:6px;height:22px;background:{PRIMARY_RED};
                        border-radius:4px;margin-right:10px;"></div>
            <div style="font-size:1.25rem;font-weight:700;color:{color};">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value):
    """Small metric tile with Toyota styling."""
    st.markdown(
        f"""
        <div style="
            border-left:4px solid {PRIMARY_RED};
            padding:0.6rem 1rem;
            background:#fafafa;
            border-radius:6px;
            margin-bottom:0.4rem;">
            <div style="font-size:0.80rem;color:{DARK_GRAY};font-weight:600;">
                {title}
            </div>
            <div style="font-size:1.25rem;font-weight:700;color:{BLACK};
                        margin-top:4px;">
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
    <h1 style='color:{PRIMARY_RED}; font-weight:800;'>
        Toyota GR – Sector Performance Dashboard
    </h1>
    <hr style="border:1px solid {DARK_GRAY}; margin-top:-8px;">
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Helper: Build lap_time_s consistently
# ---------------------------------------------------------
def build_lap_time_seconds(df):
    lap_time = pd.to_numeric(df.get("lap_time_s", np.nan), errors="coerce")

    # If large, assume ms
    lap_time = lap_time.where(lap_time < 1000, lap_time / 1000)

    for c in ["s1_seconds", "s2_seconds", "s3_seconds"]:
        if c not in df:
            df[c] = np.nan

    sector_sum = (
        pd.to_numeric(df["s1_seconds"], errors="coerce").fillna(0)
        + pd.to_numeric(df["s2_seconds"], errors="coerce").fillna(0)
        + pd.to_numeric(df["s3_seconds"], errors="coerce").fillna(0)
    )

    lap_time = lap_time.where(lap_time.notna(), sector_sum)
    return lap_time.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------
# Load processed ETL Data
# ---------------------------------------------------------
loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())

sectors = data.get("sectors", pd.DataFrame())
if sectors.empty:
    st.error("No sector data available. Ensure ETL completed successfully.")
    st.stop()

# ---------------------------------------------------------
# Track Selection
# ---------------------------------------------------------
track = st.selectbox("Select Track", meta.get_tracks())
track_sectors = sectors[sectors["track"] == track].copy()

if track_sectors.empty:
    st.error(f"No sector data for track '{track}'.")
    st.stop()

# ---------------------------------------------------------
# Standardize Columns
# ---------------------------------------------------------
cols = track_sectors.columns.tolist()

# Lap number mapping
if "lap" in cols:
    track_sectors["lap_number"] = pd.to_numeric(track_sectors["lap"], errors="coerce")
elif "lap_number" in cols:
    track_sectors["lap_number"] = pd.to_numeric(track_sectors["lap_number"], errors="coerce")
else:
    st.error("No lap index column found.")
    st.stop()

track_sectors = track_sectors.dropna(subset=["lap_number"])
track_sectors["lap_number"] = track_sectors["lap_number"].astype(int)

# Car/vehicle number
if "vehicle_number" not in track_sectors.columns:
    st.error("Missing required column: 'vehicle_number'")
    st.stop()

track_sectors["vehicle_number_str"] = (
    track_sectors["vehicle_number"].astype(str).str.strip()
)

car_list = sorted(track_sectors["vehicle_number_str"].unique(),
                  key=lambda x: int(float(x)) if x.replace(".", "", 1).isdigit() else 9999)

car_choice = st.selectbox("Select Car", car_list)

car_df = track_sectors[track_sectors["vehicle_number_str"] == car_choice].copy()
if car_df.empty:
    st.error(f"No sector data for car {car_choice}.")
    st.stop()

# Build lap times
car_df["lap_time_s"] = build_lap_time_seconds(car_df)

# Convert sector times
for sec in ["s1_seconds", "s2_seconds", "s3_seconds"]:
    car_df[sec] = pd.to_numeric(car_df.get(sec, np.nan), errors="coerce")

car_df = car_df.dropna(subset=["lap_time_s", "lap_number"]).sort_values("lap_number")

if len(car_df) < 3:
    st.warning("Not enough laps to compute sector analysis.")
    st.stop()

# ---------------------------------------------------------
# TRACK + CAR HEADER
# ---------------------------------------------------------
section_header(f"{track.capitalize()} — Car #{car_choice}")

# ---------------------------------------------------------
# Summary Metrics
# ---------------------------------------------------------
best_lap = car_df["lap_time_s"].min()
avg_lap = car_df["lap_time_s"].mean()
total_laps = int(car_df["lap_number"].max())

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Best Lap (s)", f"{best_lap:.3f}")
with c2:
    metric_card("Avg Lap (s)", f"{avg_lap:.3f}")
with c3:
    metric_card("Total Laps", total_laps)

# ---------------------------------------------------------
# Sector Averages: Car vs Field
# ---------------------------------------------------------
section_header("Sector Averages – Car vs Field")

field_df = track_sectors.copy()
for c in ["s1_seconds", "s2_seconds", "s3_seconds"]:
    field_df[c] = pd.to_numeric(field_df[c], errors="coerce")

car_mean = car_df[["s1_seconds", "s2_seconds", "s3_seconds"]].mean()
field_mean = field_df[["s1_seconds", "s2_seconds", "s3_seconds"]].mean()
delta = car_mean - field_mean

summary_tbl = pd.DataFrame({
    "Sector": ["S1", "S2", "S3"],
    "Car Mean (s)": car_mean.values,
    "Field Mean (s)": field_mean.values,
    "Delta vs Field (s)": delta.values,
})

st.dataframe(summary_tbl.style.format({
    "Car Mean (s)": "{:.3f}",
    "Field Mean (s)": "{:.3f}",
    "Delta vs Field (s)": "{:+.3f}",
}), use_container_width=True)

# ---------------------------------------------------------
# Lap Time Evolution
# ---------------------------------------------------------
section_header("Lap Time Evolution")

fig_lap = px.line(
    car_df,
    x="lap_number",
    y="lap_time_s",
    markers=True,
    color_discrete_sequence=[PRIMARY_RED],
)
fig_lap.update_layout(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=BLACK),
)
st.plotly_chart(fig_lap, use_container_width=True)

# ---------------------------------------------------------
# Sector Breakdown per Lap
# ---------------------------------------------------------
section_header("Sector Breakdown per Lap")

long_df = car_df[["lap_number", "s1_seconds", "s2_seconds", "s3_seconds"]].melt(
    id_vars="lap_number",
    var_name="sector",
    value_name="time_s",
)
long_df["sector"] = long_df["sector"].map({
    "s1_seconds": "S1",
    "s2_seconds": "S2",
    "s3_seconds": "S3",
})

fig_stack = px.bar(
    long_df,
    x="lap_number",
    y="time_s",
    color="sector",
    barmode="stack",
    color_discrete_map={"S1": PRIMARY_RED, "S2": DARK_GRAY, "S3": BLACK},
)
st.plotly_chart(fig_stack, use_container_width=True)

# ---------------------------------------------------------
# Sector Time Distribution
# ---------------------------------------------------------
section_header("Sector Time Distribution")

fig_box = px.box(
    long_df,
    x="sector",
    y="time_s",
    color="sector",
    color_discrete_map={"S1": PRIMARY_RED, "S2": DARK_GRAY, "S3": BLACK},
    points="all",
)
st.plotly_chart(fig_box, use_container_width=True)

# ---------------------------------------------------------
# Delta to Best Sector per Lap
# ---------------------------------------------------------
section_header("Delta to Best Sector per Lap")

best_by_lap = (
    field_df.dropna(subset=["lap_number"])
    .groupby("lap_number")[["s1_seconds", "s2_seconds", "s3_seconds"]]
    .min()
    .rename(columns={
        "s1_seconds": "best_s1",
        "s2_seconds": "best_s2",
        "s3_seconds": "best_s3"
    })
)

deltas = car_df[["lap_number", "s1_seconds", "s2_seconds", "s3_seconds"]].merge(
    best_by_lap, on="lap_number", how="left"
)

for s, best in zip(
        ["s1_seconds", "s2_seconds", "s3_seconds"],
        ["best_s1", "best_s2", "best_s3"]
):
    deltas[f"delta_{s}"] = deltas[s] - deltas[best]

delta_long = deltas.melt(
    id_vars="lap_number",
    value_vars=["delta_s1_seconds", "delta_s2_seconds", "delta_s3_seconds"],
    var_name="sector",
    value_name="delta_s",
)
delta_long["sector"] = delta_long["sector"].map({
    "delta_s1_seconds": "S1",
    "delta_s2_seconds": "S2",
    "delta_s3_seconds": "S3",
})

fig_delta = px.line(
    delta_long,
    x="lap_number",
    y="delta_s",
    color="sector",
    markers=True,
    color_discrete_map={"S1": PRIMARY_RED, "S2": DARK_GRAY, "S3": BLACK},
)
st.plotly_chart(fig_delta, use_container_width=True)

# ---------------------------------------------------------
# Raw data view
# ---------------------------------------------------------
section_header("Raw Sector Data")

with st.expander("View Raw Data Table"):
    cols_to_display = [
        "lap_number", "lap_time_s", "s1_seconds", "s2_seconds",
        "s3_seconds", "pit_time", "speed_kph"
    ]
    st.dataframe(car_df[[c for c in cols_to_display if c in car_df]], use_container_width=True)
