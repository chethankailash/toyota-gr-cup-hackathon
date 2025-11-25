import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import DataLoader
from utils.track_meta import TrackMeta

# ------------------------------------------------------
# PAGE CONFIG (must be first Streamlit command)
# ------------------------------------------------------
st.set_page_config(
    page_title="GR Cup Strategy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------
# FORCE LIGHT THEME + TOYOTA COLORS
# ------------------------------------------------------
st.markdown(
    """
    <style>
        :root {
            --primary-color: #EB0A1E;
            --text-color: #000000;
            --background-color: #FFFFFF;
            --secondary-background-color: #F5F5F5;
        }

        /* Main background */
        .main {
            background-color: #FFFFFF !important;
        }

        /* Sidebar background black */
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* Top menu/header */
        header[data-testid="stHeader"] {
            background-color: #FFFFFF !important;
        }
        header[data-testid="stHeader"] * {
            color: #000000 !important;
        }

        /* Page tiles */
        .tile {
            border: 2px solid #EB0A1E;
            padding: 25px;
            border-radius: 12px;
            background-color: #FFFFFF;
            transition: 0.25s;
        }

        .tile:hover {
            background-color: #EB0A1E11;
            transform: translateY(-3px);
            border-color: #EB0A1E;
        }

        .tile h3 {
            color: #EB0A1E !important;
            font-weight: 700;
        }

        .metric-card {
            background-color: #F5F5F5;
            padding: 18px;
            border-radius: 10px;
            border-left: 6px solid #EB0A1E;
        }

    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------
loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())

laps = data.get("laps", pd.DataFrame())
sectors = data.get("sectors", pd.DataFrame())
results = data.get("results", pd.DataFrame())

tracks = meta.get_tracks()

# ------------------------------------------------------
# HEADER
# ------------------------------------------------------
st.markdown(
    "<h1 style='color:#EB0A1E; font-weight:900;'>🏁 Toyota GR Cup – Strategy & Telemetry Hub</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    """
### **Welcome to the official GR Cup racing intelligence dashboard.**  
Use the panels below to navigate through race analytics, telemetry, predictions, and strategy tools.
"""
)


# ------------------------------------------------------
# TOP ROW: METRIC CARDS
# ------------------------------------------------------
st.markdown("## **📊 Championship Summary**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Total Tracks</h3>
            <h1 style="margin-top:-10px;">{len(tracks)}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    total_laps = len(laps)
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Total Recorded Laps</h3>
            <h1 style="margin-top:-10px;">{total_laps}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    total_sectors = len(sectors)
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Sector Data Points</h3>
            <h1 style="margin-top:-10px;">{total_sectors}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------
# TRACK MAP PREVIEW (simple bar chart)
# ------------------------------------------------------
st.markdown("## 🏎️ Track Dataset Coverage")

track_lap_counts = (
    laps.groupby("track")["lap"].count()
    if "lap" in laps.columns else pd.Series()
)

if not track_lap_counts.empty:
    fig = px.bar(
        track_lap_counts,
        title="Lap Count Per Track",
        labels={"value": "Lap Count", "track": "Track"},
        color_discrete_sequence=["#EB0A1E"],
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lap dataset has no lap count column — skipping chart.")

# ------------------------------------------------------
# MODULE GRID (Cleaner + Compact)
# ------------------------------------------------------
st.markdown(
    """
    <h2 style='color:#000000; margin-top: 1rem;'>Explore Dashboard Modules</h2>
    """,
    unsafe_allow_html=True
)

# Better tile CSS (compact, soft shadow, clean spacing)
st.markdown(
    """
    <style>
        .module-tile {
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            transition: transform 0.1s ease, box-shadow 0.1s ease;
        }
        .module-tile:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        }
        .module-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: #000000
            margin-bottom: 4px;
        }
        .module-desc {
            font-size: 0.78rem;
            color: #58595B;
            line-height: 1.1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">📊 Track Explorer</div>
            <div class="module-desc">
                Compare lap times, driver performance, 
                and weather influence across tracks.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">🛑 Braking Analysis</div>
            <div class="module-desc">
                Heatmaps, intensity clusters, and panic-stop detection.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">🧭 Corner Analysis</div>
            <div class="module-desc">
                Apex speed, min-speed mapping, and corner severity scoring.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">⏱ Sector Performance</div>
            <div class="module-desc">
                Evaluate per-lap sector splits and delta-to-best timelines.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">⚙ Strategy Simulator</div>
            <div class="module-desc">
                Multi-stop pit logic, tire degradation modeling,
                and race time predictions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="module-tile">
            <div class="module-title">🤖 Lap Time Forecasting</div>
            <div class="module-desc">
                Random Forest predictions based on historical telemetry.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

