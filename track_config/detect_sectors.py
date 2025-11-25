# track_config/detect_sectors.py

import duckdb
import pandas as pd


class SectorDetector:
    def __init__(self, parquet_path="data/processed/sectors.parquet"):
        self.parquet_path = parquet_path

        # Load once into memory via DuckDB → Pandas
        self.df = duckdb.query(f"""
            SELECT *
            FROM read_parquet('{self.parquet_path}')
        """).df()

        # Make sure column names are lowercased to match the ETL
        self.df.columns = [c.lower() for c in self.df.columns]

    def _get_numeric_col(self, df, candidates):
        """
        Try multiple candidate column names and return a numeric Series.
        """
        for name in candidates:
            if name in df.columns:
                return pd.to_numeric(df[name], errors="coerce")
        return None

    def detect_sectors(self, track_name: str):
        """
        Returns a dict with sector timing stats + distance ratio
        for S1/S2/S3 on a given track.
        """
        track_df = self.df[self.df["track"] == track_name]

        if track_df.empty:
            return None

        s1_series = self._get_numeric_col(track_df, ["s1_seconds", "s1"])
        s2_series = self._get_numeric_col(track_df, ["s2_seconds", "s2"])
        s3_series = self._get_numeric_col(track_df, ["s3_seconds", "s3"])

        if s1_series is None or s2_series is None or s3_series is None:
            # Missing some sector data; return what we can
            return None

        sector_summary = {
            "S1": {
                "avg_time": float(s1_series.mean()),
                "std_time": float(s1_series.std()),
                "min": float(s1_series.min()),
                "max": float(s1_series.max())
            },
            "S2": {
                "avg_time": float(s2_series.mean()),
                "std_time": float(s2_series.std()),
                "min": float(s2_series.min()),
                "max": float(s2_series.max())
            },
            "S3": {
                "avg_time": float(s3_series.mean()),
                "std_time": float(s3_series.std()),
                "min": float(s3_series.min()),
                "max": float(s3_series.max())
            },
        }

        total = (
            sector_summary["S1"]["avg_time"]
            + sector_summary["S2"]["avg_time"]
            + sector_summary["S3"]["avg_time"]
        )

        if total > 0:
            for s in ["S1", "S2", "S3"]:
                sector_summary[s]["distance_ratio"] = (
                    sector_summary[s]["avg_time"] / total
                )
        else:
            for s in ["S1", "S2", "S3"]:
                sector_summary[s]["distance_ratio"] = None

        return sector_summary
