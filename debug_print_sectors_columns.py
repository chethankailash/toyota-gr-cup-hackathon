import pandas as pd

df = pd.read_parquet("data/processed/sectors.parquet")
print("\n===== SECTORS COLUMNS =====")
for col in df.columns:
    print(col)
print("\nTotal rows:", len(df))

print("\n===== SAMPLE ROWS =====")
print(df.head(5))
