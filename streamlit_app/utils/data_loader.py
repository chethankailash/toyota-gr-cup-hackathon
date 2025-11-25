# streamlit_app/utils/data_loader.py

import pandas as pd
import json

class DataLoader:
    def __init__(self):
        self.base = "data/processed"

    def load_all(self):
        return {
            "laps": pd.read_parquet(f"{self.base}/laps_real.parquet"),
            "telemetry": pd.read_parquet(f"{self.base}/telemetry.parquet", engine="pyarrow"),
            "results": pd.read_parquet(f"{self.base}/results.parquet"),
            "weather": pd.read_parquet(f"{self.base}/weather.parquet"),
            "sectors": pd.read_parquet(f"{self.base}/sectors.parquet"),
            "bestlaps": pd.read_parquet(f"{self.base}/bestlaps.parquet"),
        }

    def load_track_metadata(self):
        with open("track_config/track_metadata.json", "r") as f:
            return json.load(f)
