import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path to enable standard imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from database import get_connection
    from timeline_service import get_timeline_service
    from tools.vision_llm_geocoder import deduce_location_from_images
except ImportError as e:
    print(f"[Error] Could not import project modules: {e}")
    sys.exit(1)

def run_retrospective_mapping():
    print("=" * 50)
    print("   GEOLOCATE PIPELINE: STARTING SYSTEM SCAN")
    print("=" * 50)

    # 1. Init Services
    print("[Init] Initializing Timeline Service index...")
    svc = get_timeline_service()
    if not svc or not svc.points:
        print("[Abort] Timeline service failed to load point data.")
        return

    # 2. Fetch target photos
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, file_path, date_taken, location_tags 
        FROM photos 
        WHERE (latitude IS NULL OR latitude = '') 
          AND date_taken IS NOT NULL 
          AND date_taken != ''
    """)
    target_photos = [dict(r) for r in c.fetchall()]
    print(f"[Scan] Found {len(target_photos)} photos missing EXIF GPS data.")

    if not target_photos:
        print("[Done] No photos require geocoding. Exiting.")
        conn.close()
        return

    # Stage 1: Timeline Mapping
    timeline_updates = []
    unmapped_photos = []
    
    print("\n[Phase 1] Running Timeline Temporal Inference...")
    processed = 0
    for photo in target_photos:
        processed += 1
        pid = photo['id']
        dt_str = photo['date_taken']
        
        # Check Timeline (60 min / 3600s threshold)
        lat, lon, delta = svc.get_closest_location(dt_str, max_delta_seconds=3600)
        
        if lat is not None:
            # Queue update
            timeline_updates.append((lat, lon, pid))
            # Minimal visual progress every 50 matches
            if len(timeline_updates) % 50 == 0:
                 print(f"   ...Matched {len(timeline_updates)} photos via Timeline history.")
        else:
            unmapped_photos.append(photo)
            
    # Apply Timeline Batch updates
    if timeline_updates:
        print(f"[DB] Writing {len(timeline_updates)} verified location points to database...")
        c.executemany("UPDATE photos SET latitude = ?, longitude = ? WHERE id = ?", timeline_updates)
        conn.commit()
        print(f"[DB] Success. Applied {len(timeline_updates)} Timeline updates.")
    else:
        print("[DB] No Timeline matches found in this dataset.")

    # Stage 2: Local LLM Fallback
    print(f"\n[Phase 2] Evaluating {len(unmapped_photos)} orphan photos for LLM Deductive Inference...")
    
    if not unmapped_photos:
        print("[Phase 2] Complete. No remaining orphans.")
        conn.close()
        return
        
    # Group orphans by directory to infer region coherently (avoids redundant LLM calls)
    groups = {}
    for p in unmapped_photos:
        dir_path = os.path.dirname(p['file_path'])
        if dir_path not in groups:
            groups[dir_path] = []
        groups[dir_path].append(p)
        
    print(f"[LLM] Partitioned orphans into {len(groups)} folder-clusters for spatial reasoning.")
    
    llm_success_count = 0
    
    # Process folder by folder
    for folder, photos_in_group in groups.items():
        if not photos_in_group: continue
        
        folder_name = os.path.basename(folder)
        print(f"\n   [LLM Cluster] Processing '{folder_name}' ({len(photos_in_group)} photos)")
        
        # Sample up to 4 valid images from folder to feed the LLM
        valid_samples = []
        for cand in photos_in_group[:10]: # Look at first 10 candidates
            if os.path.exists(cand['file_path']):
                valid_samples.append(cand['file_path'])
                if len(valid_samples) >= 1:
                    break
                    
        if not valid_samples:
             print("      SKIPPING: No readable physical image files found.")
             continue
             
        # Check current state of ollama server beforehand to prevent hanging if possible, 
        # but our function has a timeout built in.
        try:
             print(f"      Querying Vision LLM with {len(valid_samples)} samples...")
             res = deduce_location_from_images(valid_samples)
             
             if res and res.get("latitude") and res.get("longitude"):
                 est_lat = float(res["latitude"])
                 est_lon = float(res["longitude"])
                 city = res.get("city_or_region", "Unknown")
                 reason = res.get("reasoning", "N/A")
                 
                 print(f"      -> SUCCESS! LLM Deduced: {city} ({est_lat}, {est_lon}) Conf: {res.get('confidence')}")
                 print(f"      -> Reasoning: {reason[:100]}...")
                 
                 # Prepare batch update for ALL photos in this folder group
                 group_updates = [(est_lat, est_lon, photo_item['id']) for photo_item in photos_in_group]
                 c.executemany("UPDATE photos SET latitude = ?, longitude = ? WHERE id = ?", group_updates)
                 conn.commit()
                 llm_success_count += len(photos_in_group)
             else:
                 print(f"      -> LLM could not reach a confident geographical conclusion.")
        except Exception as e:
             print(f"      -> ERROR during LLM inference: {e}")
             
    print("\n" + "="*50)
    print(f"   SUMMARY")
    print(f"   Photos Analyzed:   {len(target_photos)}")
    print(f"   Timeline Matched:  {len(timeline_updates)}")
    print(f"   LLM Clusters Applied: {llm_success_count}")
    print("="*50)
    
    conn.close()

if __name__ == "__main__":
    run_retrospective_mapping()
