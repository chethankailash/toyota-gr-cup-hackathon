# models/lap_time_features.py

import pandas as pd


def prepare_lap_features(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a training-ready table from laps_real.parquet.

    Expected columns in laps_df:
      - track
      - vehicle_id
      - outing
      - lap
      - lap_time_s
      - start_time
      - end_time
    """
    df = laps_df.copy()

    # Ensure types
    df["lap"] = pd.to_numeric(df["lap"], errors="coerce")
    df["lap_time_s"] = pd.to_numeric(df["lap_time_s"], errors="coerce")
    df = df.dropna(subset=["lap", "lap_time_s"])
    df["lap"] = df["lap"].astype(int)

    # Sort to get proper temporal order
    df = df.sort_values(["track", "vehicle_id", "outing", "lap"])

    # Stint lap index: within each (track, vehicle, outing)
    df["stint_lap_idx"] = (
        df.groupby(["track", "vehicle_id", "outing"])
        .cumcount()
        .astype(int)
    )

    # Previous lap time within the same stint
    df["prev_lap_time_s"] = (
        df.groupby(["track", "vehicle_id", "outing"])["lap_time_s"]
        .shift(1)
    )

    # Rolling 3-lap avg as simple "pace" signal
    df["rolling_3_lap_time_s"] = (
        df.groupby(["track", "vehicle_id", "outing"])["lap_time_s"]
        .rolling(window=3, min_periods=1)
        .mean()
        .reset_index(level=[0, 1, 2], drop=True)
    )

    # Drop rows where prev_lap_time_s is NaN (first lap of stint)
    df = df.dropna(subset=["prev_lap_time_s"])

    # Cast to numeric
    df["prev_lap_time_s"] = df["prev_lap_time_s"].astype(float)
    df["rolling_3_lap_time_s"] = df["rolling_3_lap_time_s"].astype(float)

    return df


def get_feature_target_split(df: pd.DataFrame):
    """
    Given prepared features, return X, y and list of feature columns.
    """
    feature_cols = [
        "lap",               # absolute lap
        "stint_lap_idx",     # lap index within stint
        "prev_lap_time_s",   # previous lap time
        "rolling_3_lap_time_s",
    ]

    # One-hot encode vehicle_id (global across tracks)
    df = df.copy()
    df["vehicle_id"] = df["vehicle_id"].astype(str)
    df_oh = pd.get_dummies(df, columns=["vehicle_id"], prefix="veh")

    feature_cols_extended = feature_cols + [
        c for c in df_oh.columns
        if c.startswith("veh_")
    ]

    X = df_oh[feature_cols_extended]
    y = df_oh["lap_time_s"].astype(float)

    return X, y, feature_cols_extended
