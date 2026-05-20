import sys
import os
from datetime import datetime

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from timeline_service import get_timeline_service

svc = get_timeline_service()
res = svc.get_closest_location("2009-05-28 14:15:00")
print(f"Timeline Lookup for 2009-05-28: {res}")

# Also print earliest/latest times in index
if svc.points:
    earliest = datetime.fromtimestamp(svc.points[0][0])
    latest = datetime.fromtimestamp(svc.points[-1][0])
    print(f"Timeline covers range: {earliest} to {latest}")
else:
    print("No points loaded.")
