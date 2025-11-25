# utils/pit_stop_optimizer.py

import pandas as pd
import numpy as np


# ---------------------------------------------------------
# Universal lap time parser (handles MM:SS, HH:MM:SS, SS.sss)
# ---------------------------------------------------------
def parse_lap_time_to_seconds(x):
    if pd.isna(x):
        return np.nan
    x = str(x).strip()

    # Already numeric
    if x.replace(".", "", 1).isdigit():
        return float(x)

    parts = x.split(":")
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0]), float(parts[1])
        else:
            h, m, s = 0, 0, float(parts[0])
        return h * 3600 + m * 60 + s
    except Exception:
        return np.nan


# ---------------------------------------------------------
# Fit simple degradation model y = a + b * lap_age
# ---------------------------------------------------------
def fit_degradation_model(car_df):
    non_pit = car_df[~car_df["is_pit_lap"]].dropna(subset=["lap_number", "lap_time_s"])

    if len(non_pit) < 3:
        return None, None

    x = non_pit["lap_number"].astype(float)
    y = non_pit["lap_time_s"].astype(float)

    try:
        # polyfit returns slope, intercept
        slope, intercept = np.polyfit(x, y, 1)
        return float(intercept), float(slope)
    except Exception:
        return None, None


# ---------------------------------------------------------
# Pit loss estimation
# ---------------------------------------------------------
def estimate_pit_loss(car_df, default=25.0):
    pit_cols = [c for c in car_df.columns if "pit" in c.lower()]
    if pit_cols:
        pit_col = pit_cols[0]
        pit_vals = pd.to_numeric(car_df[pit_col], errors="coerce").dropna()
        if len(pit_vals) > 0:
            return float(pit_vals.median())
    return default


# ---------------------------------------------------------
# Generate multiple scenarios (+0, +1, +2 pit stops)
# ---------------------------------------------------------
def build_pit_scenarios(sectors_df, track, car_number, total_race_laps, default_pit_loss_s=25.0):
    df = sectors_df[sectors_df["track"] == track].copy()

    # ------------ Map lap number ------------ #
    lap_col = None
    for cand in ["lap_number", "lap", "lap_num"]:
        if cand in df.columns:
            lap_col = cand
            break

    if lap_col is None:
        return pd.DataFrame()

    # ------------ Map lap time ------------ #
    time_col = None
    for cand in ["lap_time", "laptime", "lap time"]:
        if cand in df.columns:
            time_col = cand
            break

    if time_col is None:
        return pd.DataFrame()

    # ------------ Map car number ------------ #
    car_col = None
    for cand in ["number", "car_number", "vehicle_number", "driver_number"]:
        if cand in df.columns:
            car_col = cand
            break

    if car_col is None:
        return pd.DataFrame()

    car_df = df[df[car_col] == car_number].copy()

    if car_df.empty:
        return pd.DataFrame()

    # ------------ Parse lap times ------------ #
    car_df["lap_time_s"] = car_df[time_col].apply(parse_lap_time_to_seconds)
    car_df["lap_number"] = pd.to_numeric(car_df[lap_col], errors="coerce")

    # ------------ Detect pit laps ------------ #
    pit_col = None
    for cand in df.columns:
        if "pit" in cand.lower():
            pit_col = cand
            break

    if pit_col:
        car_df["is_pit_lap"] = car_df[pit_col].fillna(0) != 0
    else:
        # heuristic: slow laps = pit laps
        med = car_df["lap_time_s"].median()
        car_df["is_pit_lap"] = car_df["lap_time_s"] > 1.25 * med

    # ------------ Cleanup -------------- #
    car_df = car_df.dropna(subset=["lap_number", "lap_time_s"])
    if len(car_df) < 4:
        return pd.DataFrame()

    # ------------ Fit degradation model ------------ #
    a, b = fit_degradation_model(car_df)
    if a is None or b is None:
        return pd.DataFrame()

    # ------------ Pit loss ------------ #
    pit_loss = estimate_pit_loss(car_df, default_pit_loss_s)

    # ------------ Simulation ------------ #
    laps = np.arange(1, total_race_laps + 1)
    base = a + b * laps

    scenario_rows = []

    for stop_lap in range(2, total_race_laps - 1):
        stint_times = []
        for lap in laps:
            if lap > stop_lap:
                age = lap - stop_lap
            else:
                age = lap
            stint_times.append(a + b * age)

        total_time = np.sum(stint_times) + pit_loss

        for lap in laps:
            scenario_rows.append({
                "lap": lap,
                "type": f"pit@{stop_lap}",
                "time_s": stint_times[lap - 1] if lap != stop_lap else stint_times[lap - 1] + pit_loss
            })

    # baseline
    for lap, lt in zip(laps, base):
        scenario_rows.append({
            "lap": lap,
            "type": "baseline",
            "time_s": float(lt)
        })

    return pd.DataFrame(scenario_rows)
