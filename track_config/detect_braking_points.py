# track_config/detect_braking_points.py

import duckdb
import pandas as pd
import os


class BrakingPointDetector:
    def __init__(self, telemetry_folder="data/processed"):
        self.telemetry_folder = telemetry_folder

    def _load_track_telemetry(self, track_name: str) -> pd.DataFrame:
        """
        Load a LIGHT subset of telemetry for a given track:
        - at most 100k rows
        - only: speed, accx_can, pbrake_f, pbrake_r
        - union_by_name=True to handle schema differences across telemetry parquet files.
        """
        pattern = os.path.join(self.telemetry_folder, f"telemetry_{track_name}_*.parquet")

        query = f"""
            SELECT *
            FROM (
                SELECT
                    *,
                    lower(telemetry_name) AS telemetry_name_lower
                FROM read_parquet('{pattern}', union_by_name=True)
            )
            WHERE telemetry_name_lower IN ('speed', 'accx_can', 'pbrake_f', 'pbrake_r')
            LIMIT 100000
        """

        try:
            df = duckdb.query(query).df()
        except Exception as e:
            print(f"[BrakingPointDetector] DuckDB error for track={track_name}: {e}")
            return pd.DataFrame()

        if df.empty:
            return df

        df_pivot = df.pivot_table(
            index=["timestamp", "lap", "vehicle_number", "track"],
            columns="telemetry_name_lower",
            values="telemetry_value",
            aggfunc="mean",
        ).reset_index()

        # Convert timestamp to epoch seconds if it is datetime
        if pd.api.types.is_datetime64_any_dtype(df_pivot["timestamp"]):
            df_pivot["timestamp"] = df_pivot["timestamp"].astype("int64") / 1e9

        # Ensure numeric
        for col in ["speed", "accx_can", "pbrake_f", "pbrake_r"]:
            if col in df_pivot.columns:
                df_pivot[col] = pd.to_numeric(df_pivot[col], errors="coerce")

        df_pivot = df_pivot.sort_values("timestamp")
        return df_pivot

    def detect_braking_points(self, track_name: str):
        """
        Light-weight braking point detection:
        - big negative speed gradient
        - strong negative longitudinal accel
        - or high brake pressure (if logged)
        """
        df = self._load_track_telemetry(track_name)
        if df.empty:
            return []

        if "speed" not in df.columns:
            print(f"[BrakingPointDetector] No speed column for track={track_name}")
            return []

        df["speed_diff"] = df["speed"].diff()

        has_accx = "accx_can" in df.columns
        has_f = "pbrake_f" in df.columns
        has_r = "pbrake_r" in df.columns

        thr_drop = -4.0    # km/h per sample
        thr_acc = -0.2     # G
        thr_brake = 5.0    # bar

        events = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]

            cond1 = row["speed_diff"] < thr_drop if not pd.isna(row["speed_diff"]) else False
            cond2 = has_accx and (row["accx_can"] < thr_acc if not pd.isna(row["accx_can"]) else False)
            cond3 = has_f and (row["pbrake_f"] > thr_brake if not pd.isna(row["pbrake_f"]) else False)
            cond4 = has_r and (row["pbrake_r"] > thr_brake if not pd.isna(row["pbrake_r"]) else False)

            if cond1 or cond2 or cond3 or cond4:
                events.append({
                    "timestamp": float(row["timestamp"]),
                    "lap": int(row["lap"]),
                    "vehicle_number": row["vehicle_number"],
                    "speed_before": float(prev["speed"]),
                    "speed_after": float(row["speed"]),
                })

        return events
