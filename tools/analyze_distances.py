import sqlite3
import os
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

DB_PATH = os.path.join('photo_manager', 'data', 'index.db')

def analyze_distances():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT encoding FROM faces WHERE person_id IS NULL')
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("No unknown faces found")
        return
    
    encodings = [np.frombuffer(r['encoding'], dtype=np.float64) for r in rows]
    encodings = np.stack(encodings)
    
    dist_matrix = euclidean_distances(encodings)
    
    print(f"Number of faces: {len(encodings)}")
    print(f"Max distance: {np.max(dist_matrix):.4f}")
    print(f"Min distance (excl self): {np.min(dist_matrix[dist_matrix > 0]):.4f}")
    print(f"Median distance: {np.median(dist_matrix):.4f}")
    
    # Sweep eps values
    from sklearn.cluster import DBSCAN
    print("\nSweep eps:")
    for eps in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        clustering = DBSCAN(eps=eps, min_samples=1, metric='euclidean').fit(encodings)
        labels = clustering.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"eps={eps:.1f}: Clusters={n_clusters}")

if __name__ == "__main__":
    analyze_distances()
