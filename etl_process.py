# etl_process.py

from utils.loader import GRDataLoader

if __name__ == "__main__":
    print("\n🚀 Starting ETL Process...")

    loader = GRDataLoader()
    data = loader.load_all_tracks()
    loader.save_parquet(data)

    print("\n✅ ETL Completed Successfully!")
