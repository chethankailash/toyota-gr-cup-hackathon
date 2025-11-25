# streamlit_app/pages/5_Pit_Stop_Optimizer.py

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
    """Standard Toyota section header with red accent bar."""
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
            <div style="font-size:1.25rem;font-weight:700;color:{color};">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value):
    """Toyota metric tile — matches other pages."""
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
        Toyota GR – Pit Stop Optimizer
    </h1>
    <hr style="border:1px solid {DARK_GRAY}; margin-top:-8px;">
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Load ETL data
# ---------------------------------------------------------
loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())
sectors = data.get("sectors", pd.DataFrame())

if sectors.empty:
    st.error("No sector data available. Run ETL first.")
    st.stop()

# ---------------------------------------------------------
# Helper: lap time construction
# ---------------------------------------------------------
def build_lap_time(df):
    """Build clean lap_time_s values."""
    # lap_time_s direct
    if "lap_time_s" in df.columns:
        lt = pd.to_numeric(df["lap_time_s"], errors="coerce")
        lt = lt.where(lt < 1000, lt / 1000)  # ms → s
    else:
        lt = pd.Series(np.nan, index=df.index)

    # fallback: sum sectors
    s1 = pd.to_numeric(df.get("s1_seconds", np.nan), errors="coerce")
    s2 = pd.to_numeric(df.get("s2_seconds", np.nan), errors="coerce")
    s3 = pd.to_numeric(df.get("s3_seconds", np.nan), errors="coerce")
    sec_sum = s1.fillna(0) + s2.fillna(0) + s3.fillna(0)

    lt = lt.where(lt.notna(), sec_sum)
    lt = lt.replace(0, np.nan)

    if lt.isna().any():
        med = lt.dropna().median() if lt.dropna().size > 0 else 120.0
        lt = lt.fillna(med)

    return lt


def clean_laps(df):
    """Ensure lap_number + cleaned lap_time_s."""
    if "lap" in df.columns:
        df["lap_number"] = pd.to_numeric(df["lap"], errors="coerce")
    elif "lap_number" in df.columns:
        df["lap_number"] = pd.to_numeric(df["lap_number"], errors="coerce")
    else:
        df["lap_number"] = np.arange(1, len(df) + 1)

    df = df[df["lap_number"] > 0].drop_duplicates("lap_number")
    df["lap_time_s"] = build_lap_time(df)

    # Clean unrealistic values
    df = df[(df["lap_time_s"] > 20) & (df["lap_time_s"] < 300)]

    # If too few laps, generate synthetic filler
    if len(df) < 5:
        missing = 5 - len(df)
        base = df["lap_time_s"].median() if len(df) else 120
        last = df["lap_number"].max() if len(df) else 0
        filler = pd.DataFrame({
            "lap_number": np.arange(last + 1, last + 1 + missing),
            "lap_time_s": base * 1.02,
            "pit_time": 0,
            "is_pit_lap": False,
        })
        df = pd.concat([df, filler], ignore_index=True)

    return df.sort_values("lap_number")


def estimate_pit_loss(df):
    """Pit loss estimation."""
    if "pit_time" in df.columns:
        pt = pd.to_numeric(df["pit_time"], errors="coerce").dropna()
        if len(pt) > 0 and pt.median() > 0:
            return float(pt.median())

    # fallback: slow laps
    med = df["lap_time_s"].median()
    slowlaps = df[df["lap_time_s"] > med * 1.2]["lap_time_s"]
    if len(slowlaps) > 0:
        return float(slowlaps.median() - med)

    return 20.0


def fit_degradation(df):
    """Linear a + b*lap degradation fit."""
    base = df[df["is_pit_lap"] == False]
    if len(base) < 4:
        return float(base["lap_time_s"].median()), 0.02

    x = base["lap_number"].values
    y = base["lap_time_s"].values
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def simulate(df, a, b, pit_loss):
    laps = int(df["lap_number"].max())
    seq = np.arange(1, laps + 1)

    no_pit = (a + b * seq).sum()

    out = []
    for stops in [0, 1, 2]:
        out.append({
            "Strategy": f"{stops} Stop(s)",
            "total_time_s": no_pit + stops * pit_loss
        })

    return pd.DataFrame(out)


# ---------------------------------------------------------
# UI – Track and Car Selectors
# ---------------------------------------------------------
track = st.selectbox("Select Track", meta.get_tracks())
track_df = sectors[sectors["track"] == track]

if "vehicle_number" not in track_df.columns:
    st.error("Missing vehicle_number in sector data.")
    st.stop()

cars = sorted(track_df["vehicle_number"].dropna().unique())
car = st.selectbox("Select Car", cars)

car_df = track_df[track_df["vehicle_number"] == car].copy()
car_df["is_pit_lap"] = car_df.get("pit_time", 0).fillna(0) > 1.0
car_df = clean_laps(car_df)

# ---------------------------------------------------------
# Compute model parameters
# ---------------------------------------------------------
pit_loss = estimate_pit_loss(car_df)
a, b = fit_degradation(car_df)

section_header("Model Estimates")

col1, col2, col3 = st.columns(3)
col1.metric("Pit Loss (s)", f"{pit_loss:.1f}")
col2.metric("Base Pace (a)", f"{a:.3f}")
col3.metric("Degradation (b)", f"{b:+.4f}")

# ---------------------------------------------------------
# Strategy Simulation
# ---------------------------------------------------------
section_header("Strategy Comparison")

res = simulate(car_df, a, b, pit_loss)
res["total_time_min"] = res["total_time_s"] / 60

best = res.loc[res["total_time_s"].idxmin()]

st.success(
    f"Best Strategy: **{best['Strategy']}** "
    f"({best['total_time_min']:.2f} min)"
)

fig = px.bar(
    res,
    x="Strategy",
    y="total_time_min",
    text="total_time_min",
    color="Strategy",
    color_discrete_map={
        "0 Stop(s)": PRIMARY_RED,
        "1 Stop(s)": DARK_GRAY,
        "2 Stop(s)": BLACK,
    }
)
fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Cleaned Data Table
# ---------------------------------------------------------
section_header("Cleaned Lap Data")
st.dataframe(car_df.reset_index(drop=True), use_container_width=True)
