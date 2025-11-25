# utils/loader.py

import os
import pandas as pd
import duckdb
from utils.normalizer import normalize_columns


class GRDataLoader:
    def __init__(self, raw_path="data/raw", processed_path="data/processed"):
        self.raw_path = raw_path
        self.processed_path = processed_path

        self.lap_start = []
        self.lap_end = []
        self.laps = []
        self.telemetry = []
        self.results = []
        self.weather = []
        self.sectors = []
        self.bestlaps = []

    # ---------------------------------------------------------
    # Public: load all tracks
    # ---------------------------------------------------------
    def load_all_tracks(self):
        print(f"\n🔍 Scanning folder: {self.raw_path}")

        for track in os.listdir(self.raw_path):
            track_path = os.path.join(self.raw_path, track)
            if not os.path.isdir(track_path):
                continue

            print("\n============================")
            print(f"📁 Track: {track}")
            print("============================")

            for file in os.listdir(track_path):
                if file.lower().endswith(".csv"):
                    self._load_single_file(os.path.join(track_path, file), track)

        return self._combine()

    # ---------------------------------------------------------
    # Internal: clean semicolon-based sector CSVs
    # ---------------------------------------------------------
    def _read_sectors_csv(self, path, track):
        print("   ↳ semicolon CSV detected")

        try:
            df = pd.read_csv(path, sep=";", engine="python")
        except Exception:
            df = pd.read_csv(path, engine="python")

        df = normalize_columns(df)
        df["track"] = track

        # Convert any *_seconds columns
        for col in df.columns:
            if "seconds" in col:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Lap time cleanup
        if "lap_time" in df.columns:
            df["lap_time"] = pd.to_numeric(df["lap_time"], errors="coerce")

        return df

    # ---------------------------------------------------------
    # Internal: file classifier
    # ---------------------------------------------------------
    def _load_single_file(self, path, track):
        file_lower = path.lower()
        print(f"\n📄 Processing: {path}")

        # -------------------- Telemetry --------------------
        if "telemetry" in file_lower:
            print("➡️ TELEMETRY (DuckDB)")

            os.makedirs(self.processed_path, exist_ok=True)
            out_parquet = os.path.join(
                self.processed_path,
                f"telemetry_{track}_{os.path.basename(path)}.parquet",
            )

            duckdb.query(f"""
                COPY (
                    SELECT *, '{track}' AS track
                    FROM read_csv_auto('{path}')
                ) TO '{out_parquet}' (FORMAT 'parquet');
            """)

            self.telemetry.append(out_parquet)
            return

        # -------------------- SECTORS -----------------------
        if "analysis" in file_lower or "endurance" in file_lower:
            print("➡️ SECTORS/ANALYSIS (cleaning & cast)")
            df = self._read_sectors_csv(path, track)
            self.sectors.append(df)
            return

        # -------------------- Pandas CSV --------------------
        df = pd.read_csv(path)
        df = normalize_columns(df)
        df["track"] = track

        # LAP START
        if "lap_start" in file_lower:
            print("➡️ LAP_START")
            self.lap_start.append(df)
            return

        # LAP END
        if "lap_end" in file_lower:
            print("➡️ LAP_END")
            self.lap_end.append(df)
            return

        # LAP TIME
        if "lap_time" in file_lower or "_lap_time" in file_lower:
            print("➡️ LAP_TIME")
            self.laps.append(df)
            return

        # BEST LAPS
        if "best" in file_lower and "lap" in file_lower:
            print("➡️ BESTLAPS")
            self.bestlaps.append(df)
            return

        # WEATHER
        if "weather" in file_lower:
            print("➡️ WEATHER")
            self.weather.append(df)
            return

        # RESULTS
        if "results" in file_lower or "provisional" in file_lower:
            print("➡️ RESULTS")
            self.results.append(df)
            return

        print(f"⚠️ UNCLASSIFIED FILE — {path}")

    # ---------------------------------------------------------
    # Combine multiple DataFrames safely
    # ---------------------------------------------------------
    @staticmethod
    def _fix_duplicate_columns(df):
        df = df.copy()
        df.columns = df.columns.astype(str)
        return df.loc[:, ~df.columns.duplicated()]

    def _combine(self):
        print("\n🔧 Combining datasets...")

        def safe_concat(list_df):
            if not list_df:
                return pd.DataFrame()
            cleaned = [self._fix_duplicate_columns(df) for df in list_df]
            return pd.concat(cleaned, ignore_index=True, sort=False)

        return {
            "laps": safe_concat(self.laps),
            "lap_start": safe_concat(self.lap_start),
            "lap_end": safe_concat(self.lap_end),
            "telemetry": self.telemetry,
            "results": safe_concat(self.results),
            "weather": safe_concat(self.weather),
            "sectors": safe_concat(self.sectors),
            "bestlaps": safe_concat(self.bestlaps),
        }

    # ---------------------------------------------------------
    # Save to parquet
    # ---------------------------------------------------------
    def save_parquet(self, data_dict):
        os.makedirs(self.processed_path, exist_ok=True)

        for name, df in data_dict.items():
            if name == "telemetry":
                print(f"💾 Telemetry saved as {len(df)} parquet file(s)")
                continue

            df = df.copy()
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].astype(str)

            path = os.path.join(self.processed_path, f"{name}.parquet")
            df.to_parquet(path, index=False)
            print(f"💾 Saved {name}: {len(df)} rows -> {path}")
