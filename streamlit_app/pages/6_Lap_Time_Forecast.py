# streamlit_app/pages/6_Lap_Time_Forecast.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor

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
# UI COMPONENTS (Shared Across App)
# ---------------------------------------------------------
def section_header(text, color=BLACK):
    """Toyota red accent bar + black section title."""
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
    """Toyota metric card with red accent."""
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
        Toyota GR – Lap Time Forecasting (ML Model)
    </h1>
    <hr style="border:1px solid {DARK_GRAY}; margin-top:-8px;">
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Load ETL Data
# ---------------------------------------------------------
loader = DataLoader()
data = loader.load_all()
meta = TrackMeta(loader.load_track_metadata())
sectors = data.get("sectors", pd.DataFrame())

if sectors.empty:
    st.error("No lap/sector data. Run ETL first.")
    st.stop()


# ---------------------------------------------------------
# Helper: Build Clean Lap Times
# ---------------------------------------------------------
def build_lap_time(df):
    """Preferred: lap_time_s → fallback: sum of sector times."""
    if "lap_time_s" in df.columns:
        lt = pd.to_numeric(df["lap_time_s"], errors="coerce")
        lt = lt.where(lt < 1000, lt / 1000)  # ms → seconds
    else:
        lt = pd.Series(np.nan, index=df.index)

    # Fallback: sum sectors
    s1 = pd.to_numeric(df.get("s1_seconds", np.nan), errors="coerce")
    s2 = pd.to_numeric(df.get("s2_seconds", np.nan), errors="coerce")
    s3 = pd.to_numeric(df.get("s3_seconds", np.nan), errors="coerce")

    sec_sum = s1.fillna(0) + s2.fillna(0) + s3.fillna(0)
    lt = lt.where(lt.notna(), sec_sum)

    # Fallback median fill
    med = lt.dropna().median() if len(lt.dropna()) else 120.0
    lt = lt.fillna(med)

    return lt


# ---------------------------------------------------------
# Select Track & Car
# ---------------------------------------------------------
track = st.selectbox("Select Track", meta.get_tracks())

track_df = sectors[sectors["track"] == track].copy()

if "vehicle_number" not in track_df.columns:
    st.error("Missing vehicle_number column in sector data.")
    st.stop()

cars = sorted(track_df["vehicle_number"].dropna().unique())
car = st.selectbox("Select Car", cars)

df = track_df[track_df["vehicle_number"] == car].copy()


# ---------------------------------------------------------
# Build Lap Numbers
# ---------------------------------------------------------
if "lap" in df.columns:
    df["lap_number"] = pd.to_numeric(df["lap"], errors="coerce")
elif "lap_number" in df.columns:
    df["lap_number"] = pd.to_numeric(df["lap_number"], errors="coerce")
else:
    df["lap_number"] = np.arange(1, len(df) + 1)

df = df[df["lap_number"] > 0].drop_duplicates("lap_number")


# ---------------------------------------------------------
# Clean Lap Time Column
# ---------------------------------------------------------
df["lap_time_s"] = build_lap_time(df)
df = df[(df["lap_time_s"] > 20) & (df["lap_time_s"] < 300)]
df = df.sort_values("lap_number")

if len(df) < 8:
    st.warning("Not enough valid laps for ML model (need ≥ 8 laps).")
    st.stop()


# ---------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------
df["prev_lap_time"] = df["lap_time_s"].shift(1)
df["rolling_avg_3"] = df["lap_time_s"].rolling(3).mean()
df["lap_delta"] = df["lap_time_s"].diff()
df.fillna(method="bfill", inplace=True)

features = ["lap_number", "prev_lap_time", "rolling_avg_3", "lap_delta"]
target = "lap_time_s"

X = df[features]
y = df[target]


# ---------------------------------------------------------
# Train ML Model
# ---------------------------------------------------------
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=6,
    random_state=42
)
model.fit(X, y)


# ---------------------------------------------------------
# Forecast Future Laps
# ---------------------------------------------------------
section_header("Forecast Configuration")

future_laps = st.slider("Number of Future Laps to Predict", 3, 15, 5)

last_lap = int(df["lap_number"].max())
prev_time = df["lap_time_s"].iloc[-1]
roll = df["rolling_avg_3"].iloc[-1]
delta = df["lap_delta"].iloc[-1]

future_rows = []

for i in range(1, future_laps + 1):
    lap_num = last_lap + i

    X_pred = pd.DataFrame([{
        "lap_number": lap_num,
        "prev_lap_time": prev_time,
        "rolling_avg_3": roll,
        "lap_delta": delta
    }])

    pred = model.predict(X_pred)[0]

    future_rows.append({
        "lap_number": lap_num,
        "predicted_lap_time_s": pred
    })

    # Update sequential features (rolling)
    delta = pred - prev_time
    prev_time = pred
    roll = (roll * 2 + pred) / 3

future_df = pd.DataFrame(future_rows)


# ---------------------------------------------------------
# VISUALIZATIONS
# ---------------------------------------------------------
section_header(f"Lap Time Trend — {track}, Car {car}")

# Actual lap time trend
fig_actual = px.line(
    df,
    x="lap_number",
    y="lap_time_s",
    markers=True,
    color_discrete_sequence=[PRIMARY_RED],
)
fig_actual.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_actual, use_container_width=True)


# Forecasted lap times
section_header("Forecasted Lap Times")

fig_forecast = px.line(
    future_df,
    x="lap_number",
    y="predicted_lap_time_s",
    markers=True,
    color_discrete_sequence=[DARK_GRAY],
)
fig_forecast.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_forecast, use_container_width=True)


# Combined view
section_header("Actual vs Forecast Comparison")

combined = pd.concat([
    df[["lap_number", "lap_time_s"]].rename(columns={"lap_time_s": "time"}),
    future_df.rename(columns={"predicted_lap_time_s": "time"})
])

combined["type"] = ["Actual"] * len(df) + ["Forecast"] * len(future_df)

fig_combo = px.line(
    combined,
    x="lap_number",
    y="time",
    color="type",
    markers=True,
    color_discrete_map={"Actual": PRIMARY_RED, "Forecast": DARK_GRAY},
)

fig_combo.update_layout(paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=BLACK))

st.plotly_chart(fig_combo, use_container_width=True)


# ---------------------------------------------------------
# RAW DATA TABLES
# ---------------------------------------------------------
section_header("Cleaned Lap Data")
st.dataframe(df.reset_index(drop=True), use_container_width=True)

section_header("Forecast Table")
st.dataframe(future_df, use_container_width=True)
