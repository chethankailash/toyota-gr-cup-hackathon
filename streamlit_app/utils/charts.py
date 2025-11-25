# streamlit_app/utils/charts.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def lap_time_chart(laps_df, track):
    df = laps_df[laps_df["track"] == track]

    if df.empty:
        return go.Figure()

    fig = px.scatter(
        df,
        x="lap",
        y="lap_time_s",
        color="vehicle_id",
        title=f"Lap Times – {track}",
        labels={"lap_time_s": "Lap Time (s)", "lap": "Lap"}
    )
    fig.update_traces(mode="lines+markers")
    return fig


def braking_heatmap(braking_points):
    if not braking_points:
        return go.Figure()

    df = pd.DataFrame(braking_points)

    fig = px.histogram(
        df,
        x="timestamp",
        nbins=40,
        title="Braking Density Over Time"
    )
    return fig


def corner_speed_plot(corners):
    if not corners:
        return go.Figure()

    df = pd.DataFrame(corners)

    fig = px.scatter(
        df,
        x="start_time",
        y="min_speed",
        size="max_lateral_g",
        title="Corner Intensity vs Speed"
    )
    return fig
