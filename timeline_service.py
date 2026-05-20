import json
import os
import re
from datetime import datetime
import bisect
import dateutil.parser

TIMELINE_FILE = r"C:\Users\admin\Downloads\Timeline.json"

class TimelineService:
    def __init__(self, filepath=TIMELINE_FILE):
        self.filepath = filepath
        self.points = []  # List of tuples: (timestamp, lat, lng)
        self.is_loaded = False

    def load(self):
        """Loads and parses the Timeline JSON file into memory sorted by timestamp."""
        if not os.path.exists(self.filepath):
            print(f"[Timeline] Error: File not found at {self.filepath}")
            return False

        print(f"[Timeline] Loading and parsing {self.filepath}...")
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[Timeline] JSON Parse Error: {e}")
            return False

        temp_points = []
        segments = data.get("semanticSegments", [])
        print(f"[Timeline] Scanning {len(segments)} semantic segments...")

        for segment in segments:
            # Path 1: timelinePath points (Precise movement)
            if "timelinePath" in segment:
                for p in segment["timelinePath"]:
                    try:
                        dt = dateutil.parser.parse(p["time"])
                        ts = dt.timestamp()
                        lat, lon = self._parse_latlng_string(p["point"])
                        if lat is not None and lon is not None:
                            temp_points.append((ts, lat, lon))
                    except:
                        continue

            # Path 2: visits (Static location duration)
            if "visit" in segment:
                try:
                    visit = segment["visit"]
                    # Use startTime for entry
                    dt = dateutil.parser.parse(segment["startTime"])
                    ts = dt.timestamp()
                    cand = visit.get("topCandidate", {})
                    loc = cand.get("placeLocation", {})
                    
                    # Some use "latLng" field string, some might use numeric if different format, but based on sample it's a string
                    if "latLng" in loc:
                        lat, lon = self._parse_latlng_string(loc["latLng"])
                        if lat is not None and lon is not None:
                            temp_points.append((ts, lat, lon))
                except:
                    continue

        # Sort for binary search
        temp_points.sort(key=lambda x: x[0])
        self.points = temp_points
        self.is_loaded = True
        print(f"[Timeline] Ingested {len(self.points)} geo-temporal data points.")
        return True

    def _parse_latlng_string(self, s):
        """Converts '28.3880004°, 77.3070685°' to (28.3880004, 77.3070685)."""
        try:
            # Replace degree symbol and split
            clean = s.replace('°', '').replace(' ', '')
            parts = clean.split(',')
            return float(parts[0]), float(parts[1])
        except:
            return None, None

    def get_closest_location(self, target_iso_or_dt, max_delta_seconds=3600):
        """
        Finds the closest geographical point within max_delta_seconds threshold.
        Returns (lat, lng, delta_sec) or (None, None, None).
        """
        if not self.is_loaded:
            if not self.load():
                return None, None, None
        
        if not self.points:
            return None, None, None

        try:
            if isinstance(target_iso_or_dt, str):
                # Handle common EXIF colons format before parsing
                ts_str = target_iso_or_dt
                if re.match(r'^\d{4}:\d{2}:\d{2} ', ts_str):
                     ts_str = ts_str.replace(':', '-', 2)
                target_ts = dateutil.parser.parse(ts_str).timestamp()
            else:
                target_ts = target_iso_or_dt.timestamp()
        except Exception as e:
            return None, None, None

        # Binary search setup
        timestamps = [p[0] for p in self.points]
        idx = bisect.bisect_left(timestamps, target_ts)

        candidates = []
        if idx < len(self.points):
            candidates.append(self.points[idx])
        if idx > 0:
            candidates.append(self.points[idx - 1])

        best_match = None
        min_diff = float('inf')

        for ts, lat, lon in candidates:
            diff = abs(target_ts - ts)
            if diff < min_diff and diff <= max_delta_seconds:
                min_diff = diff
                best_match = (lat, lon, diff)

        if best_match:
            return best_match
        return None, None, None

# Global singleton placeholder for direct Python reuse
_global_instance = None
def get_timeline_service():
    global _global_instance
    if _global_instance is None:
        _global_instance = TimelineService()
        _global_instance.load()
    return _global_instance

if __name__ == "__main__":
    # Quick sanity test
    svc = TimelineService()
    svc.load()
    # Sample time from the file provided in initial output: 2014-04-03T10:26:00.000+05:30
    res = svc.get_closest_location("2014-04-03T10:30:00")
    print(f"Test Lookup Result: {res}")
