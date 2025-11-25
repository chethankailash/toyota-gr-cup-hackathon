class TrackMeta:
    def __init__(self, metadata):
        self.meta = metadata

    def get_tracks(self):
        return list(self.meta.keys())

    def corners(self, track):
        return self.meta.get(track, {}).get("corners", [])

    def braking(self, track):
        return self.meta.get(track, {}).get("braking_points", [])

    def sectors(self, track):
        return self.meta.get(track, {}).get("sectors", [])
