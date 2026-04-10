import pandas as pd
import numpy as np
from math import radians
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import AgglomerativeClustering
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


# ---- Load and prepare data ----
df = pd.read_csv(r"C:\users\david\downloads\taxi_flow_kepler_bronx_only.csv")
df = df[['origin_lat', 'origin_lng', 'dest_lat', 'dest_lng']].dropna()

# ---- Normalize direction (A→B == B→A) ----
def normalize_trip(row):
    a = (row['origin_lat'], row['origin_lng'])
    b = (row['dest_lat'], row['dest_lng'])
    return pd.Series(sorted([a, b]), index=['origin', 'destination'])

norm = df.apply(normalize_trip, axis=1)
df['norm_origin_lat'] = norm['origin'].apply(lambda x: x[0])
df['norm_origin_lng'] = norm['origin'].apply(lambda x: x[1])
df['norm_dest_lat'] = norm['destination'].apply(lambda x: x[0])
df['norm_dest_lng'] = norm['destination'].apply(lambda x: x[1])

# ---- Convert to radians ----
coords = np.radians(df[['norm_origin_lat', 'norm_origin_lng', 'norm_dest_lat', 'norm_dest_lng']].values)

# ---- Custom haversine+max distance metric in 4D ----
def haversine_batch(a, b):
    dlat = a[:, 0] - b[:, 0]
    dlon = a[:, 1] - b[:, 1]
    lat1 = a[:, 0]
    lat2 = b[:, 0]
    tmp = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    return 2 * np.arcsin(np.sqrt(tmp))

def trip_distance_matrix(coords, k=15, radius_rad=0.5 / 3958.8):
    n = coords.shape[0]
    neighbors = NearestNeighbors(metric='euclidean', n_neighbors=k, n_jobs=-1)
    neighbors.fit(coords)
    knn_dists, knn_indices = neighbors.kneighbors(coords)

    rows, cols, data = [], [], []

    for i in range(n):
        for j in knn_indices[i]:
            if i >= j: continue  # Avoid duplicate entries
            o_dist = haversine_batch(coords[i:i+1, 0:2], coords[j:j+1, 0:2])[0]
            d_dist = haversine_batch(coords[i:i+1, 2:4], coords[j:j+1, 2:4])[0]
            dist = max(o_dist, d_dist)
            if dist <= radius_rad:
                rows.extend([i, j])
                cols.extend([j, i])
                data.extend([dist, dist])
    return csr_matrix((data, (rows, cols)), shape=(n, n))

print("🔧 Building sparse distance graph...")
sparse_graph = trip_distance_matrix(coords, k=15)

print("🔎 Finding connected components...")
n_components, labels_cc = connected_components(csgraph=sparse_graph, directed=False, return_labels=True)

print(f"🔢 Found {n_components} connected components")

# Reuse coordinate array
all_labels = np.full(coords.shape[0], fill_value=-1, dtype=int)
next_cluster_id = 0

for component_id in range(n_components):
    indices = np.where(labels_cc == component_id)[0]
    if len(indices) == 1:
        all_labels[indices[0]] = next_cluster_id
        next_cluster_id += 1
        continue

    sub_coords = coords[indices]
    sub_graph = sparse_graph[indices][:, indices]

    # 🔍 Detect sub-subgraphs in this component
    n_sub, sub_labels_cc = connected_components(sub_graph, directed=False, return_labels=True)

    for sub_component_id in range(n_sub):
        sub_indices = np.where(sub_labels_cc == sub_component_id)[0]
        global_indices = indices[sub_indices]

        if len(global_indices) == 1:
            all_labels[global_indices[0]] = next_cluster_id
            next_cluster_id += 1
            continue

        sub_sub_coords = coords[global_indices]
        sub_sub_graph = sub_graph[sub_indices][:, sub_indices]

        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=0.5 / 3958.8,
            linkage='complete',
            connectivity=sub_sub_graph
        )

        sub_labels = model.fit_predict(sub_sub_coords)
        for local_idx, global_idx in enumerate(global_indices):
            all_labels[global_idx] = next_cluster_id + sub_labels[local_idx]

        next_cluster_id += sub_labels.max() + 1

df['cluster'] = all_labels
# ---- Aggregate results ----
print("📊 Aggregating clusters...")
grouped = df.groupby('cluster').agg(
    trip_count=('cluster', 'count'),
    origin_lat=('norm_origin_lat', 'mean'),
    origin_lng=('norm_origin_lng', 'mean'),
    dest_lat=('norm_dest_lat', 'mean'),
    dest_lng=('norm_dest_lng', 'mean')
).reset_index(drop=True)

grouped.to_csv(r"C:\users\david\downloads\bus_routes\KNN_grouped_trips.csv", index=False)
print(r"✅ Done. Saved to C:\users\david\downloads\bus_routes\KNN_grouped_trips.csv")
