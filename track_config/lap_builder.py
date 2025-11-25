import pandas as pd
import os

START_PATH = "data/processed/lap_start.parquet"
END_PATH   = "data/processed/lap_end.parquet"
OUTPUT     = "data/processed/laps_real.parquet"

print("🔧 Loading start/end lap data...")

df_start = pd.read_parquet(START_PATH)
df_end   = pd.read_parquet(END_PATH)

# Convert timestamps
df_start["timestamp"] = pd.to_datetime(df_start["timestamp"])
df_end["timestamp"]   = pd.to_datetime(df_end["timestamp"])

print("⏱ Merging start/end lap records...")

# Merge on fields that uniquely identify a lap
merge_cols = ["track", "vehicle_id", "outing", "lap"]

df = df_start.merge(
    df_end,
    on=merge_cols,
    how="inner",
    suffixes=("_start", "_end")
)

print(f"➡️ Merged rows: {len(df)}")

# Compute lap time
df["lap_time_s"] = (df["timestamp_end"] - df["timestamp_start"]).dt.total_seconds()

# Clean up the DataFrame
final_cols = [
    "track",
    "vehicle_id",
    "vehicle_number_start",
    "outing",
    "lap",
    "timestamp_start",
    "timestamp_end",
    "lap_time_s",
]

# Some lap files may not contain vehicle_number
if "vehicle_number_start" not in df.columns:
    df["vehicle_number_start"] = None

df_final = df[final_cols].rename(columns={
    "vehicle_number_start": "vehicle_number",
    "timestamp_start": "start_time",
    "timestamp_end": "end_time"
})

# Drop invalid or negative laps
df_final = df_final[df_final["lap_time_s"] > 0]

print("💾 Saving:", OUTPUT)
df_final.to_parquet(OUTPUT, index=False)

print("✅ Lap rebuild completed successfully!")
