# streamlit_app/pages/3_Braking_Analysis.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import DataLoader
from utils.track_meta import TrackMeta
from utils.theme import apply_toyota_theme

# Apply Toyota theme
apply_toyota_theme()

# -------------------------------------------------------
# Toyota GR Theme
# -------------------------------------------------------
TOYOTA_RED = "#EB0A1E"
TOYOTA_GRAY = "#58595B"
BLACK = "#000000"
WHITE = "#FFFFFF"

st.set_page_config(layout="wide")


# -------------------------------------------------------
# UI Helpers — Consistent with all other pages
# -------------------------------------------------------
def toyota_title(text):
    """Top page title in Toyota Red"""
    st.markdown(
        f"<h1 style='color:{TOYOTA_RED}; font-weight:900; margin-bottom:1rem;'>{text}</h1>",
        unsafe_allow_html=True,
    )

def toyota_section(label):
    """Section header with red bar and black text"""
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; margin-top:1.5rem; margin-bottom:0.8rem;">
            <div style="width:6px; height:22px; background:{TOYOTA_RED};
                        border-radius:6px; margin-right:10px;"></div>
            <div style="font-size:1.1rem; font-weight:700; color:{BLACK};">
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def toyota_card(title, value):
    """Metric card matching Track + Corner pages"""
    st.markdown(
        f"""
        <div style="
            border-left:4px solid {TOYOTA_RED};
            padding:0.7rem 1rem;
            background:#fafafa;
            border-radius:6px;
            margin-bottom:0.6rem;
        ">
            <div style="font-size:0.85rem; color:{TOYOTA_GRAY};">{title}</div>
            <div style="font-size:1.25rem; font-weight:700; color:{BLACK};
                        margin-top:4px;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------
# Page Title
# -------------------------------------------------------
toyota_title("Toyota GR — Braking Analysis")


# -------------------------------------------------------
# Load Sector Data
# -------------------------------------------------------
loader = DataLoader()
meta = TrackMeta(loader.load_track_metadata())
sectors = loader.load_all()["sectors"]

if sectors.empty:
    st.error("No sector data found. Please run ETL again.")
    st.stop()


# -------------------------------------------------------
# Track Selection
# -------------------------------------------------------
track = st.selectbox("Select Track", meta.get_tracks())
df = sectors[sectors["track"] == track].copy()

if df.empty:
    st.error(f"No sector data available for track: {track}")
    st.stop()


# -------------------------------------------------------
# Required Columns
# -------------------------------------------------------
required_cols = [
    "vehicle_number", "lap", "s1_seconds", "s2_seconds",
    "s3_seconds", "lap_improvement", "speed_kph"
]

# Clean casting
df["vehicle_number"] = df["vehicle_number"].astype(str)
df["lap"] = pd.to_numeric(df["lap"], errors="coerce")
df["s1_seconds"] = pd.to_numeric(df["s1_seconds"], errors="coerce")
df["s2_seconds"] = pd.to_numeric(df["s2_seconds"], errors="coerce")
df["s3_seconds"] = pd.to_numeric(df["s3_seconds"], errors="coerce")
df["speed_kph"] = pd.to_numeric(df["speed_kph"], errors="coerce")
df["lap_improvement"] = pd.to_numeric(df["lap_improvement"], errors="coerce")

df = df.dropna(subset=["lap"])


# -------------------------------------------------------
# Braking Metrics
# -------------------------------------------------------

# Sector variability — braking indicator
df["sector_variability"] = (
    df["s1_seconds"].fillna(0) +
    df["s2_seconds"].fillna(0) +
    df["s3_seconds"].fillna(0)
)

# Speed drop = braking event indicator
df = df.sort_values(["vehicle_number", "lap"])
df["speed_drop"] = df.groupby("vehicle_number")["speed_kph"].diff() * -1
df["speed_drop"] = df["speed_drop"].clip(lower=0).fillna(0)

# Braking Score
df["braking_score"] = (
    df["sector_variability"] * 0.6 +
    df["speed_drop"] * 0.4 +
    df["lap_improvement"].abs() * 0.1
)
df["braking_score"] = df["braking_score"].fillna(0)


# -------------------------------------------------------
# Summary Cards
# -------------------------------------------------------
toyota_section("Braking Summary")

c1, c2, c3 = st.columns(3)

with c1:
    toyota_card("Total Braking Events", f"{len(df)}")

with c2:
    toyota_card("Average Sector Variability", f"{df['sector_variability'].mean():.2f} s")

with c3:
    toyota_card("Average Speed Drop (km/h)", f"{df['speed_drop'].mean():.2f}")


# -------------------------------------------------------
# Heatmap — Braking Timeline
# -------------------------------------------------------
toyota_section("Braking Timeline Heatmap")

if df["braking_score"].sum() == 0:
    st.info("Insufficient data to generate braking heatmap.")
else:
    heat_df = df.groupby("lap")["braking_score"].mean().reset_index()

    fig = go.Figure(data=go.Heatmap(
        z=[heat_df["braking_score"]],
        x=heat_df["lap"],
        colorscale="Reds",
        showscale=True
    ))

    fig.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        height=280,
        margin=dict(l=10, r=10, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------
# Histogram — Speed Loss Distribution
# -------------------------------------------------------
toyota_section("Speed Loss Distribution")

if df["speed_drop"].sum() == 0:
    st.info("Speed drop data unavailable for this track.")
else:
    fig = px.histogram(
        df[df["speed_drop"] > 0],
        x="speed_drop",
        nbins=40,
        color_discrete_sequence=[TOYOTA_RED],
        title=""
    )
    fig.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(color=BLACK),
    )
    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------
# Driver Comparison — Braking Score
# -------------------------------------------------------
toyota_section("Driver Braking Comparison")

driver_brake = (
    df.groupby("vehicle_number")["braking_score"]
    .mean()
    .reset_index()
    .sort_values("braking_score", ascending=False)
)

fig = px.bar(
    driver_brake,
    x="vehicle_number",
    y="braking_score",
    color_discrete_sequence=[TOYOTA_RED],
    labels={"vehicle_number": "Car #", "braking_score": "Braking Score"},
)
fig.update_layout(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=BLACK),
)
st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------
# Debug / Raw Data
# -------------------------------------------------------
toyota_section("Raw Braking Data")
with st.expander("View Raw Data Table"):
    st.dataframe(df.head(300), use_container_width=True)
