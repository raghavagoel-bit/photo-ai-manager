import sqlite3
import os
import reverse_geocoder as rg
import dateutil.parser as dparser
import sys
import statistics

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

DB_PATH = os.path.join("data", "index.db")

COUNTRY_MAP = {
    'TR': 'Turkey',
    'KE': 'Kenya',
    'TZ': 'Tanzania',
    'UG': 'Uganda',
    'RW': 'Rwanda'
}

def parse_time(t_str):
    if not t_str or t_str == "None": return None
    try:
        return dparser.parse(t_str.replace(':', '-', 2))
    except:
        return None

def get_collection_root(path):
    # Normalized path: D:/Photos/Kenya/Go Pro/img.jpg
    # Root: D:/Photos/Kenya
    parts = path.replace('\\', '/').split('/')
    if len(parts) > 3:
        return "/".join(parts[:3]) # D:/Photos/Kenya
    return os.path.dirname(path)

def hydrate():
    if not os.path.exists(DB_PATH):
        print(f"[RECOVERY ERROR] DB not found at {DB_PATH}")
        return

    print("--- Collection-Level GPS ULTIMA Engine (V3.1-ULTIMA) ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Step 1: Fetch all photos
    c.execute("SELECT id, file_path, location_tags, latitude, longitude, date_taken FROM photos")
    photos = [dict(r) for r in c.fetchall()]
    print(f"Loaded {len(photos)} records.")

    # Step 2: Phase 1 - Extraction of Root Collections & Harvester
    print("\n[Phase 1] Harvesting Collection-Level GPS Centroids...")
    collection_gps = {} # root_path -> {lats: [], lons: [], tags: set()}
    
    for p in photos:
        root = get_collection_root(p['file_path'])
        if root not in collection_gps:
            collection_gps[root] = {'lats': [], 'lons': [], 'tags': set()}
            
        if p['latitude'] is not None and p['longitude'] is not None:
            collection_gps[root]['lats'].append(p['latitude'])
            collection_gps[root]['lons'].append(p['longitude'])

    # Step 3: Phase 2 - Geocoding Centroids and Forward Geocoding Fallbacks
    print("\n[Phase 2] Resolving Geographic Anchors...")
    cluster_anchors = {} # root_path -> (lat, lon, tags)
    
    roots_to_geocode = [r for r, data in collection_gps.items() if data['lats']]
    if roots_to_geocode:
        coords = [
            (statistics.mean(collection_gps[r]['lats']), statistics.mean(collection_gps[r]['lons'])) 
            for r in roots_to_geocode
        ]
        results = rg.search(coords)
        
        for r, lat_lon, loc in zip(roots_to_geocode, coords, results):
            cc = loc['cc']
            country = COUNTRY_MAP.get(cc, cc)
            name = loc['name']
            tags = f"{name}, {country}"
            cluster_anchors[r] = (lat_lon[0], lat_lon[1], tags)
            print(f"   Anchor: {r} -> {tags} ({len(collection_gps[r]['lats'])} GPS hits found)")
            
    # Forward Geocoding Fallback
    DEFAULT_COUNTRY_COORDS = {
        'Italy': (41.8719, 12.5674, "Italy"),
        'Turkey': (38.9637, 35.2433, "Turkey"),
        'Kenya': (-1.2921, 36.8219, "Kenya"),
        'Tanzania': (-6.3690, 34.8888, "Tanzania"),
        'Uganda': (1.3733, 32.2903, "Uganda"),
        'Rwanda': (-1.9403, 29.8739, "Rwanda"),
        'Maldives': (3.2028, 73.2207, "Maldives"),
        'India': (20.5937, 78.9629, "India")
    }
    
    roots_without_gps = [r for r, data in collection_gps.items() if not data['lats']]
    for r in roots_without_gps:
        root_name = os.path.basename(r).strip()
        if root_name in DEFAULT_COUNTRY_COORDS:
            lat, lon, tag = DEFAULT_COUNTRY_COORDS[root_name]
            cluster_anchors[r] = (lat, lon, tag)
            print(f"   Fallback Anchor (Forward Geocoding): {r} -> {tag}")

    # Step 4: Phase 3 - Massive Mirroring (The Push)
    print("\n[Phase 3] Executing Collection-Level GPS Mirroring...")
    mirrored_count = 0
    for p in photos:
        root = get_collection_root(p['file_path'])
        if root in cluster_anchors:
            lat, lon, tags = cluster_anchors[root]
            # Mirror the GPS IF the photo doesn't have its own explicit coordinates
            # OR if its current coordinates exactly match the generic country fallback (enabling upgrades)
            # Use rounding to avoid float precision issues
            def fmt_coord(f): return round(float(f), 4) if f is not None else None
            
            is_at_country_center = (fmt_coord(p['latitude']), fmt_coord(p['longitude'])) == (fmt_coord(lat), fmt_coord(lon))
            
            if p['latitude'] is None or is_at_country_center:
                p['inferred_lat'] = lat
                p['inferred_lon'] = lon
                p['inferred_tags'] = tags
                p['is_inferred'] = True 
                if p['latitude'] is None: mirrored_count += 1
            else:
                p['inferred_tags'] = tags
                p['is_inferred'] = False

    # Step 5: Phase 4 - Folder Name Rescue (Secondary Tags)
    print("\n[Phase 4] Fine-Grained Folder Discovery...")
    folder_rescued = 0
    noise = {'JPEG', 'JPG', 'none', 'None', '', 'none,', 'jpg', 'jpeg'}
    
    for p in photos:
        existing = p.get('inferred_tags', p['location_tags'] or "")
        parts = {t.strip() for t in existing.replace(',', ' ').split() if t.strip() not in noise}
        
        path_parts = p['file_path'].replace('\\', '/').split('/')
        if len(path_parts) > 2:
            potential_tags = [path_parts[-2], path_parts[-3]] if len(path_parts) > 3 else [path_parts[-2]]
            for pt in potential_tags:
                if pt not in parts and pt not in noise and len(pt) > 2 and not pt.isdigit():
                    parts.add(pt)
                    folder_rescued += 1
        
        p['final_tags'] = ", ".join(sorted(list(parts)))

    # Step 7: Phase 6 - Visual Landmark Anchoring (V3.3 NEW)
    print("\n[Phase 6] Visual Landmark Distillation (Precision Engine)...")
    from visual_geocoder import identify_location
    visual_anchors_found = 0
    
    # We map coordinates back to country names for CLIP lookups
    COORD_TO_COUNTRY = { (round(v[0], 4), round(v[1], 4)): k for k, v in DEFAULT_COUNTRY_COORDS.items() }
    
    # We only run visual geocoding on photos anchored to known generic country centroids
    candidates = []
    print(f"   [DEBUG] COORD_TO_COUNTRY keys: {list(COORD_TO_COUNTRY.keys())}")
    
    for p in photos:
        if p.get('is_inferred'):
            pos = (round(p.get('inferred_lat'), 4), round(p.get('inferred_lon'), 4))
            if pos in COORD_TO_COUNTRY:
                p['v_country_match'] = COORD_TO_COUNTRY[pos]
                candidates.append(p)
            else:
                pass # print(f"   [DEBUG] Photo {p['id']} is inferred but coords {pos} not in map")
        
    print(f"   Analyzing {len(candidates)} generic country anchors for landmarks...")
    
    for p in candidates:
        country = p['v_country_match']
        result = identify_location(p['file_path'], country)
        if result:
            name, lat, lon, conf = result
            p['inferred_lat'] = lat
            p['inferred_lon'] = lon
            p['final_tags'] = f"{name}, {p['final_tags']}"
            visual_anchors_found += 1
            p['v_upgraded'] = True
            print(f"   [MATCH] Photo {p['id']} -> {name} ({conf:.2f})")
        else:
            p['v_upgraded'] = False

    # Phase 7: Vision LLM Deductive Geocoding (V3.4)
    print("\n[Phase 7] Vision LLM Deductive Geocoding (V3.4)...")
    from vision_llm_geocoder import deduce_location_from_images
    import random
    import requests
    llm_upgraded_count = 0
    
    # 1. Filter out photos that have precise GPS (not inferred) or were upgraded by CLIP
    llm_candidates = [p for p in candidates if not p.get('v_upgraded')]
    
    # 2. Group by folder
    llm_folders = {}
    for p in llm_candidates:
        root = get_collection_root(p['file_path'])
        if root not in llm_folders:
            llm_folders[root] = []
        llm_folders[root].append(p)
        
    for root, root_photos in llm_folders.items():
        print(f"   Analyzing folder for LLM cues: {root} ({len(root_photos)} photos)")
        # 3. Sample 3-5 images
        sample_size = min(len(root_photos), 4)
        samples = random.sample(root_photos, sample_size)
        sample_paths = [s['file_path'] for s in samples]
        
        country_hint = root_photos[0].get('v_country_match', 'Unknown Location')
        
        # 4. Query LLM
        llm_result = deduce_location_from_images(sample_paths, country_hint)
        if llm_result and llm_result.get('confidence') == 'high' and llm_result.get('city_or_region'):
            deduced_loc = llm_result['city_or_region']
            reasoning = llm_result.get('reasoning', '')
            print(f"   [LLM SUCCESS] Deduced Location: {deduced_loc} (Reasoning: {reasoning})")
            
            # 5. Geocode using Nominatim API (OpenStreetMap)
            try:
                osm_url = f"https://nominatim.openstreetmap.org/search?q={deduced_loc}&format=json&limit=1"
                headers = {'User-Agent': 'Antigravity/PhotoManagerV3.4'}
                resp = requests.get(osm_url, headers=headers).json()
                if resp:
                    new_lat = float(resp[0]['lat'])
                    new_lon = float(resp[0]['lon'])
                    
                    # Apply to all photos in this folder
                    for p in root_photos:
                        p['inferred_lat'] = new_lat
                        p['inferred_lon'] = new_lon
                        p['final_tags'] = f"{deduced_loc}, {p['final_tags']}"
                        llm_upgraded_count += 1
                    print(f"      -> Mapped {deduced_loc} to ({new_lat}, {new_lon}). Applied to {len(root_photos)} photos.")
                else:
                    print(f"      -> Failed to map {deduced_loc} to coordinates.")
            except Exception as e:
                print(f"      -> Geocoding error: {e}")
        else:
            print(f"   [LLM NO MATCH] Could not deduce a precise location with high confidence.")

    # Step 8: Final - Database Write
    print(f"\n[Final] Global Database Update...")
    update_data = []
    for p in photos:
        update_data.append((
            p['final_tags'],
            p.get('inferred_lat', p['latitude']),
            p.get('inferred_lon', p['longitude']),
            p['id']
        ))

    c.executemany("UPDATE photos SET location_tags = ?, latitude = ?, longitude = ? WHERE id = ?", update_data)
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] V3.4-CARTOGRAPHY HYDRATION COMPLETE.")
    print(f"   GPS Sync: {mirrored_count} photos anchored to collection roots.")
    print(f"   Visual Anchors: {visual_anchors_found} photos upgraded to precision landmarks (CLIP).")
    print(f"   LLM Geocoding: {llm_upgraded_count} photos upgraded via Vision LLM.")
    print(f"   Tag Sync: {folder_rescued} collection-level tags restored.")

if __name__ == "__main__":
    hydrate()
