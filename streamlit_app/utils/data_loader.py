# streamlit_app/utils/data_loader.py

import pandas as pd
import json
import streamlit as st
from huggingface_hub import hf_hub_download


class DataLoader:
    """
    Loads all parquet files directly from HuggingFace instead of local disk.
    This ensures Streamlit Cloud works without bundling large datasets.
    """

    def __init__(self):
        # Your dataset repo
        self.repo_id = "Chethankailashnath/grcup-parquet-data"
        self.repo_type = "dataset"
        self.cache_dir = "./hf_cache"  # Streamlit will persist this between runs

        # Exact filenames — unchanged from your local environment
        self.files = {
            "laps": "laps_real.parquet",
            "telemetry": "telemetry.parquet",
            "results": "results.parquet",
            "weather": "weather.parquet",
            "sectors": "sectors.parquet",
            "bestlaps": "bestlaps.parquet",
        }

    @st.cache_data(show_spinner=True)
    def _download(_, repo_id, filename, repo_type, cache_dir):
        """
        Cached download from HuggingFace Hub.
        Returns a local temporary file path.
        """
        return hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type=repo_type,
            cache_dir=cache_dir
        )

    def _load_parquet(self, fname):
        """
        Download → read parquet
        """
        local_path = self._download(
            self.repo_id,
            fname,
            self.repo_type,
            self.cache_dir
        )
        return pd.read_parquet(local_path)

    def load_all(self):
        """
        Load every dataset your dashboard uses.
        """
        return {
            key: self._load_parquet(fname)
            for key, fname in self.files.items()
        }

    def load_track_metadata(self):
        """
        Track metadata remains local (small JSON file).
        """
        with open("track_config/track_metadata.json", "r") as f:
            return json.load(f)
