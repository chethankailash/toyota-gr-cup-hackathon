import pandas as pd

starts = pd.read_parquet("data/processed/lap_start.parquet")
ends = pd.read_parquet("data/processed/lap_end.parquet")

print("\nStart columns:", starts.columns)
print("End columns:", ends.columns)

print("\nExample start rows:")
print(starts.head())

print("\nExample end rows:")
print(ends.head())

print("\nTracks in lap_start:", starts['track'].unique())
print("Tracks in lap_end:", ends['track'].unique())
