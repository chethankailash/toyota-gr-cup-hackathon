# track_config/builder.py

import json
import os
import numpy as np

from detect_sectors import SectorDetector
from detect_corners import CornerDetector
from detect_braking_points import BrakingPointDetector


TRACKS = [
    "sonoma",
    "indy",
    "cota",
    "road_america",
    "virginia",
    "barber",
    "sebring",
]


def to_native(obj):
    """
    Recursively convert numpy types to native Python types
    so json.dump() won't choke on np.int64/np.float64/etc.
    """
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_)):
        return bool(obj)
    return obj


class TrackConfigBuilder:
    def __init__(self):
        self.sector_detector = SectorDetector()
        self.corner_detector = CornerDetector()
        self.brake_detector = BrakingPointDetector()

    def build(self):
        metadata = {}

        for track in TRACKS:
            print(f"🛠 Building metadata for {track}...")

            sectors = self.sector_detector.detect_sectors(track)
            corners = self.corner_detector.detect_corners(track)
            braking_points = self.brake_detector.detect_braking_points(track)

            metadata[track] = {
                "sectors": sectors,
                "corners": corners,
                "braking_points": braking_points,
            }

        # Convert all numpy types to native Python before JSON dump
        metadata_clean = to_native(metadata)

        os.makedirs("track_config", exist_ok=True)
        out_file = os.path.join("track_config", "track_metadata.json")

        with open(out_file, "w") as f:
            json.dump(metadata_clean, f, indent=4)

        print(f"✅ Track metadata saved → {out_file}")


if __name__ == "__main__":
    builder = TrackConfigBuilder()
    builder.build()
