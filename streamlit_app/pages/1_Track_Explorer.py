# streamlit_app/pages/1_Track_Explorer.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_loader import DataLoader
from utils.track_meta import TrackMeta
from utils.charts import lap_time_chart

from utils.theme import apply_toyota_theme
apply_toyota_theme()

# ---------------------------------------------------------
# Toyota Theme Constants
# ---------------------------------------------------------
TOYOTA_RED = "#EB0A1E"
TOYOTA_GRAY = "#58595B"
BLACK = "#000000"
WHITE = "#FFFFFF"


# ---------------------------------------------------------
# UI Helpers (Reusable)
# ---------------------------------------------------------
def toyota_section_header(label, color=BLACK):
    """Section header without emojis, black text, Toyota red bar."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;
                    margin-top:1.0rem;margin-bottom:0.4rem;">
            <div style="width:6px;height:22px;background:{TOYOTA_RED};
                        border-radius:6px;margin-right:10px;"></div>
            <div style="font-size:1.1rem;font-weight:700;color:{color};">
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def toyota_tag(text, bg=BLACK, fg=WHITE):
    st.markdown(
        f"""
        <span style="
            background:{bg};
            color:{fg};
            padding:4px 10px;
            border-radius:999px;
            font-size:0.75rem;
            font-weight:600;
            letter-spacing:0.5px;
        ">
            {text}
        </span>
        """,
        unsafe_allow_html=True,
    )


def toyota_card(title, value):
    """Metric card with Toyota red accent."""
    st.markdown(
        f"""
        <div style="
            border-left:4px solid {TOYOTA_RED};
            padding:0.6rem 1rem;
            background:#f9f9f9;
            border-radius:6px;
            margin-bottom:0.5rem;
        ">
            <div style="font-size:0.78rem;color:{TOYOTA_GRAY};">{title}</div>
            <div style="font-size:1.25rem;font-weight:700;color:{BLACK};margin-top:2px;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
st.markdown(
    f"<h1 style='color:{TOYOTA_RED}; font-weight:900; margin-bottom:0;'>Toyota GR — Track Explorer</h1>",
    unsafe_allow_html=True,
)

loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())

laps = data.get("laps", pd.DataFrame())
sectors = data.get("sectors", pd.DataFrame())
weather = data.get("weather", pd.DataFrame())
results = data.get("results", pd.DataFrame())

track = st.selectbox("Select Track", meta.get_tracks())

# ---------------------------------------------------------
# 1. LAP TIMING OVERVIEW
# ---------------------------------------------------------
toyota_section_header("Lap Time Overview")

if laps.empty:
    st.warning("No lap data available.")
else:
    toyota_tag("Lap Times Scatter Plot")
    fig = lap_time_chart(laps, track)
    fig.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(color=BLACK),
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------
# 2. DRIVER LAP TIME SPREAD
# ---------------------------------------------------------
toyota_section_header("Lap Time Spread by Driver")

track_laps = laps[laps["track"] == track].copy()

if not track_laps.empty:
    if "vehicle_number" in track_laps.columns:
        # detect lap time column
        laptime_col = None
        for cand in ["lap_time_s", "value", "laptime"]:
            if cand in track_laps.columns:
                laptime_col = cand
                break

        if laptime_col:
            track_laps["vehicle_number_str"] = (
                track_laps["vehicle_number"].astype(str)
                .str.replace(".0$", "", regex=True)
            )

            fig2 = px.box(
                track_laps,
                x="vehicle_number_str",
                y=laptime_col,
                color="vehicle_number_str",
                title=f"Lap Time Distribution by Driver – {track}",
            )
            fig2.update_layout(
                paper_bgcolor=WHITE,
                plot_bgcolor=WHITE,
                font=dict(color=BLACK),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Unable to detect lap time column.")
    else:
        st.info("This track lacks driver/vehicle identifiers.")
else:
    st.info("No lap data available for this track.")


# ---------------------------------------------------------
# 3. SECTOR PERFORMANCE SUMMARY
# ---------------------------------------------------------
toyota_section_header("Sector Performance Summary")

sec_cols = ["s1_seconds", "s2_seconds", "s3_seconds"]
track_sec = sectors[sectors["track"] == track].copy()

if not track_sec.empty and all(col in track_sec.columns for col in sec_cols):
    for col in sec_cols:
        track_sec[col] = pd.to_numeric(track_sec[col], errors="coerce")

    summary = track_sec[sec_cols].describe().T[["mean", "min", "max"]].round(3)
    summary.index = ["Sector 1", "Sector 2", "Sector 3"]

    st.dataframe(summary, use_container_width=True)
else:
    st.info("Sector columns missing for this track.")


# ---------------------------------------------------------
# 4. WEATHER SNAPSHOT
# ---------------------------------------------------------
toyota_section_header("Weather Snapshot")

track_weather = weather[weather["track"] == track].copy()

if track_weather.empty:
    st.info("Weather data not found for this track.")
else:
    track_weather = track_weather.fillna("–")
    last = track_weather.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        toyota_card("Air Temp (°C)", last.get("air_temp", "–"))
    with col2:
        toyota_card("Track Temp (°C)", last.get("track_temp", "–"))
    with col3:
        toyota_card("Humidity (%)", last.get("humidity", "–"))
    with col4:
        toyota_card("Wind Speed", last.get("wind_speed", "–"))

    with st.expander("Full Weather Data"):
        st.dataframe(track_weather, use_container_width=True)


# ---------------------------------------------------------
# 5. DRIVER LEADERBOARD
# ---------------------------------------------------------
toyota_section_header("Driver Leaderboard")

track_results = results[results["track"] == track].copy()

if track_results.empty:
    st.info("No classification results for this track.")
else:
    track_results = track_results.fillna("–")

    # Ranking logic
    if "position" in track_results.columns:
        track_results["pos_rank"] = pd.to_numeric(track_results["position"], errors="coerce")
        track_results = track_results.sort_values("pos_rank")
    else:
        track_results["pos_rank"] = np.arange(1, len(track_results) + 1)

    # Build table
    display_cols = ["pos_rank"]
    for col in ["number", "vehicle_number", "driver_name", "car"]:
        if col in track_results.columns:
            display_cols.append(col)
    for col in ["total_time", "gap_first", "laps"]:
        if col in track_results.columns:
            display_cols.append(col)

    final_tbl = track_results[display_cols].rename(columns={
        "pos_rank": "Position",
        "number": "Car #",
        "vehicle_number": "Car #",
        "driver_name": "Driver"
    })

    st.dataframe(final_tbl.reset_index(drop=True), use_container_width=True)

    with st.expander("Full Results Table"):
        st.dataframe(track_results, use_container_width=True)
