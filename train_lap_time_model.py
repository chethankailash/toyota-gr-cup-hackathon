# train_lap_time_model.py

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from models.lap_time_features import prepare_lap_features, get_feature_target_split

PROCESSED_LAPS = "data/processed/laps_real.parquet"
MODELS_DIR = "models"


def train_per_track():
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"📥 Loading laps from {PROCESSED_LAPS} ...")
    laps = pd.read_parquet(PROCESSED_LAPS)

    # Build full feature table
    print("🧱 Building features...")
    feat_df = prepare_lap_features(laps)

    tracks = sorted(feat_df["track"].unique())
    print("Tracks detected:", tracks)

    for track in tracks:
        print(f"\n🏁 Training model for track: {track}")
        df_track = feat_df[feat_df["track"] == track].copy()

        if len(df_track) < 50:
            print(f"⚠️ Not enough data for track {track}, skipping ({len(df_track)} rows).")
            continue

        X, y, feature_cols = get_feature_target_split(df_track)

        # Simple baseline model
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            n_jobs=-1,
        )

        model.fit(X, y)
        preds = model.predict(X)
        rmse = np.sqrt(((preds - y) ** 2).mean())
        print(f"✅ {track} — trained on {len(y)} samples, RMSE ~ {rmse:.3f} s")

        artifact = {
            "model": model,
            "feature_cols": feature_cols,
        }

        out_path = os.path.join(MODELS_DIR, f"lap_time_{track}.pkl")
        joblib.dump(artifact, out_path)
        print(f"💾 Saved model → {out_path}")


if __name__ == "__main__":
    train_per_track()
