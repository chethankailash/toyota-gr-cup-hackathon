# streamlit_app/pages/2_Corner_Analysis.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import DataLoader
from utils.track_meta import TrackMeta
from utils.charts import corner_speed_plot

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
# UI Helpers
# ---------------------------------------------------------
def toyota_section(label, color=BLACK):
    """Section header without emojis, clean Toyota red indicator."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;
                    margin-top:1.2rem;margin-bottom:0.6rem;">
            <div style="width:6px;height:22px;background:{TOYOTA_RED};
                        border-radius:6px;margin-right:10px;"></div>
            <div style="font-size:1.15rem;font-weight:700;color:{color};">
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def toyota_card(title, value):
    """Simple Toyota metric card."""
    st.markdown(
        f"""
        <div style="
            border-left:4px solid {TOYOTA_RED};
            padding:0.7rem 1rem;
            background:#fafafa;
            border-radius:6px;
            margin-bottom:0.4rem;
        ">
            <div style="font-size:0.85rem;color:{TOYOTA_GRAY};">{title}</div>
            <div style="font-size:1.25rem;font-weight:700;color:{BLACK};
                        margin-top:4px;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Page title (Toyota Red)
# ---------------------------------------------------------
st.markdown(
    f"<h1 style='color:{TOYOTA_RED}; font-weight:900; margin-bottom:0;'>Toyota GR — Corner Analysis</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
loader = DataLoader()
meta = TrackMeta(loader.load_track_metadata())

track = st.selectbox("Select Track", meta.get_tracks())

corners = meta.corners(track)
corners_df = pd.DataFrame(corners)


# ---------------------------------------------------------
# Basic validation
# ---------------------------------------------------------
if corners_df.empty:
    st.warning("No corner metadata found for this track.")
    st.stop()

# Normalize numeric fields
for col in ["min_speed", "max_lateral_g", "entry_speed", "exit_speed"]:
    if col in corners_df.columns:
        corners_df[col] = pd.to_numeric(corners_df[col], errors="coerce")

corners_df["corner_number"] = corners_df.index + 1


# ---------------------------------------------------------
# 1 — Overview Metrics
# ---------------------------------------------------------
toyota_section("Corner Overview")

col1, col2, col3 = st.columns(3)

with col1:
    toyota_card("Total Corners", len(corners_df))

with col2:
    avg_speed = corners_df["min_speed"].mean()
    toyota_card("Average Apex Speed (km/h)", f"{avg_speed:.1f}")

with col3:
    avg_g = corners_df["max_lateral_g"].mean()
    toyota_card("Average Lateral G", f"{avg_g:.2f}")


# ---------------------------------------------------------
# 2 — Scatter Plot (Speed vs G-force)
# ---------------------------------------------------------
toyota_section("Speed vs Lateral G-Force")

fig = corner_speed_plot(corners)
fig.update_layout(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=BLACK),
)
st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------
# 3 — Corner Difficulty Score
# ---------------------------------------------------------
toyota_section("Corner Difficulty Score")

# Heuristic difficulty model
corners_df["difficulty"] = (
    (corners_df["max_lateral_g"] * 2.5)
    + (100 - corners_df["min_speed"]) * 0.1
)

difficulty_fig = px.bar(
    corners_df,
    x="corner_number",
    y="difficulty",
    labels={"corner_number": "Corner", "difficulty": "Difficulty Score"},
    title="Corner Difficulty Ranking",
    color="difficulty",
    color_continuous_scale=[TOYOTA_GRAY, TOYOTA_RED],
)
difficulty_fig.update_layout(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=BLACK),
)
st.plotly_chart(difficulty_fig, use_container_width=True)


# ---------------------------------------------------------
# 4 — Entry vs Exit Speed
# ---------------------------------------------------------
toyota_section("Entry vs Exit Speed")

if "entry_speed" in corners_df.columns and "exit_speed" in corners_df.columns:
    delta_df = corners_df.copy()
    delta_df["speed_gain"] = delta_df["exit_speed"] - delta_df["entry_speed"]

    fig3 = px.bar(
        delta_df,
        x="corner_number",
        y="speed_gain",
        title="Speed Difference (Exit – Entry)",
        labels={"corner_number": "Corner", "speed_gain": "Δ Speed (km/h)"},
        color="speed_gain",
        color_continuous_scale=[TOYOTA_RED, "#4CAF50"],
    )
    fig3.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(color=BLACK),
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Entry and exit speed metrics unavailable for this track.")


# ---------------------------------------------------------
# 5 — Radar Chart (Corner Profile)
# ---------------------------------------------------------
toyota_section("Corner Profile Radar")

radar_df = corners_df[["corner_number", "min_speed", "max_lateral_g"]].copy()
radar_df["min_speed_norm"] = radar_df["min_speed"] / radar_df["min_speed"].max()
radar_df["g_norm"] = radar_df["max_lateral_g"] / radar_df["max_lateral_g"].max()

radar_fig = go.Figure()

radar_fig.add_trace(go.Scatterpolar(
    r=radar_df["min_speed_norm"],
    theta=radar_df["corner_number"].astype(str),
    fill='toself',
    name="Apex Speed",
    line=dict(color=TOYOTA_RED),
))

radar_fig.add_trace(go.Scatterpolar(
    r=radar_df["g_norm"],
    theta=radar_df["corner_number"].astype(str),
    fill='toself',
    name="Lateral G",
    line=dict(color=TOYOTA_GRAY),
))

radar_fig.update_layout(
    polar=dict(bgcolor=WHITE),
    showlegend=True,
    paper_bgcolor=WHITE,
    title="Corner Profile Overview (Normalized)",
)
st.plotly_chart(radar_fig, use_container_width=True)


# ---------------------------------------------------------
# 6 — Raw Data
# ---------------------------------------------------------
toyota_section("Raw Corner Metadata")

with st.expander("View Table"):
    st.dataframe(corners_df, use_container_width=True)

with st.expander("View JSON"):
    st.json(corners)
