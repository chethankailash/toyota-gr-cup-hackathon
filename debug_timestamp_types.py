import pandas as pd

df_start = pd.read_parquet("data/processed/lap_start.parquet")
df_end = pd.read_parquet("data/processed/lap_end.parquet")

print("\nStart timestamp dtype:", df_start["timestamp"].dtype)
print("End timestamp dtype:", df_end["timestamp"].dtype)

print("\nSample start:", df_start["timestamp"].head())
print("Sample end:", df_end["timestamp"].head())
