# utils/normalizer.py

import pandas as pd

# Mapping of semantic meaning -> possible CSV column names
COLUMN_MAP = {
    "vehicle_number": [
        "NUMBER", "vehicle_number", "CAR_NUMBER", "CAR NO", "NO", "PIC"
    ],
    "vehicle_id": [
        "vehicle_id", "VEHICLE_ID", "original_vehicle_id", "ECM Car Id"
    ],
    "driver_number": [
        "DRIVER_NUMBER", "DRIVER NUMBER"
    ],
    "lap": [
        "lap", "Lap", "LAP_NUMBER", "LAP_NUM", "LAP NO"
    ],
    "lap_time_s": [
        "LAP_TIME", "FL_TIME", "BEST_LAP_TIME", "value", "ELAPSED", "TOTAL_TIME"
    ],
    "timestamp": [
        "timestamp", "TIME_UTC_SECONDS", "TIME_UTC", "TIME_UTC_STR"
    ],
    "speed_kph": [
        "KPH", "FL_KPH", "TOP_SPEED"
    ],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize inconsistent column names across tracks into a common schema
    where possible, and clean basic formatting.
    """
    rename_map = {}

    upper_candidates = {k: [c.upper() for c in v] for k, v in COLUMN_MAP.items()}

    for col in df.columns:
        col_upper = col.strip().upper()
        for target, candidates in upper_candidates.items():
            if col_upper in candidates:
                rename_map[col] = target

    df = df.rename(columns=rename_map)

    # Normalize all column names to lower snake-ish
    df.columns = [c.strip().lower() for c in df.columns]

    return df
