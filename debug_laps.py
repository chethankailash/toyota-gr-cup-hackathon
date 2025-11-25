import pandas as pd

df = pd.read_parquet("data/processed/laps.parquet")

tracks = df["track"].unique()
print("\nTracks found:", tracks)

for t in tracks:
    subset = df[df["track"] == t]
    print(f"\n===== {t} =====")
    print("Rows:", len(subset))
    print("Columns:", list(subset.columns))

    # show first 5 rows
    print(subset.head())
