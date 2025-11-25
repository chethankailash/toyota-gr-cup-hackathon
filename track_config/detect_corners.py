# track_config/detect_corners.py

import duckdb
import pandas as pd
import os


class CornerDetector:
    def __init__(self, telemetry_folder="data/processed"):
        # telemetry_{track}_*.parquet written by ETL
        self.telemetry_folder = telemetry_folder

    def _load_track_telemetry(self, track_name: str) -> pd.DataFrame:
        """
        Load a LIGHTWEIGHT subset of telemetry for a given track:
        - at most 100k rows
        - only: speed, accy_can, steering_angle
        - uses union_by_name=True to tolerate schema differences across files
        """
        pattern = os.path.join(self.telemetry_folder, f"telemetry_{track_name}_*.parquet")

        # DuckDB SQL; union_by_name=True handles missing columns between R1/R2 etc.
        query = f"""
            SELECT *
            FROM (
                SELECT
                    *,
                    lower(telemetry_name) AS telemetry_name_lower
                FROM read_parquet('{pattern}', union_by_name=True)
            )
            WHERE telemetry_name_lower IN ('speed', 'accy_can', 'steering_angle')
            LIMIT 100000
        """

        try:
            df = duckdb.query(query).df()
        except Exception as e:
            print(f"[CornerDetector] DuckDB error for track={track_name}: {e}")
            return pd.DataFrame()

        if df.empty:
            return df

        # Pivot to wide format: one row per timestamp/lap/vehicle
        df_pivot = df.pivot_table(
            index=["timestamp", "lap", "vehicle_number", "track"],
            columns="telemetry_name_lower",
            values="telemetry_value",
            aggfunc="mean",
        ).reset_index()

        # Ensure numeric timestamp (epoch seconds), not pandas.Timestamp
        if pd.api.types.is_datetime64_any_dtype(df_pivot["timestamp"]):
            df_pivot["timestamp"] = df_pivot["timestamp"].astype("int64") / 1e9

        # Ensure numeric telemetry columns
        for col in ["speed", "accy_can", "steering_angle"]:
            if col in df_pivot.columns:
                df_pivot[col] = pd.to_numeric(df_pivot[col], errors="coerce")

        df_pivot = df_pivot.sort_values("timestamp")
        return df_pivot

    def detect_corners(self, track_name: str, steering_threshold=5, min_segment=8):
        """
        Very light-weight corner detection using:
        - steering angle deviation
        - lateral G
        on a capped subset of telemetry (<= 100k rows).
        """
        df = self._load_track_telemetry(track_name)
        if df.empty:
            return []

        required = {"speed", "accy_can", "steering_angle"}
        if not required.issubset(df.columns):
            print(f"[CornerDetector] Missing needed columns for track={track_name}")
            return []

        corners = []
        in_corner = False
        start_idx = None

        for i in range(len(df)):
            angle = df.iloc[i]["steering_angle"]
            lat_g = df.iloc[i]["accy_can"]

            if pd.isna(angle) or pd.isna(lat_g):
                continue

            # Start of corner: big steering or lateral G
            if not in_corner and (abs(angle) > steering_threshold or abs(lat_g) > 0.15):
                in_corner = True
                start_idx = i

            # End of corner: steering & lat G drop back near zero
            if in_corner and abs(angle) < 3 and abs(lat_g) < 0.1:
                end_idx = i
                if end_idx - start_idx > min_segment:
                    seg = df.iloc[start_idx:end_idx]

                    corners.append({
                        "start_time": float(seg["timestamp"].min()),
                        "end_time": float(seg["timestamp"].max()),
                        "min_speed": float(seg["speed"].min()),
                        "max_lateral_g": float(seg["accy_can"].abs().max()),
                        "entry_speed": float(seg["speed"].iloc[0]),
                        "exit_speed": float(seg["speed"].iloc[-1]),
                        "lap": int(seg["lap"].iloc[0]),
                    })
                in_corner = False

        return corners
