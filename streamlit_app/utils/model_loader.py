# streamlit_app/utils/model_loader.py

import os
import joblib


class ModelLoader:
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir

    def available_tracks(self):
        tracks = []
        if not os.path.isdir(self.models_dir):
            return tracks

        for f in os.listdir(self.models_dir):
            if f.startswith("lap_time_") and f.endswith(".pkl"):
                track = f.replace("lap_time_", "").replace(".pkl", "")
                tracks.append(track)
        return sorted(tracks)

    def load_model_for_track(self, track: str):
        path = os.path.join(self.models_dir, f"lap_time_{track}.pkl")
        if not os.path.exists(path):
            return None
        return joblib.load(path)
