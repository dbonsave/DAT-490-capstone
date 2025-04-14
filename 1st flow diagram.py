import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import matplotlib.colors as mcolors
from matplotlib.colors import PowerNorm


# Load trip data
df = pd.read_parquet(r"C:\Users\David\Downloads\fhvhv_tripdata_2025-01.parquet")

# Filter for top N most common routes

flow_counts = df.groupby(['PULocationID', 'DOLocationID']).size().reset_index(name='trip_count')
# Define allowed LocationIDs
# Define allowed pickup zones
# Define allowed pickup zones (as before)
# Set of allowed pickup zones
allowed_ids = {
    200, 240, 220, 241, 174, 259, 254, 81, 51, 184, 46, 3, 32, 18, 136,
    31, 20, 185, 242, 183, 58, 208, 213, 235, 169, 47, 78, 59, 60, 248,
    182, 212, 199, 167, 168, 159, 250, 94, 117
}

# Filter trips that originate in allowed zones but drop off elsewhere
df_external = df[
    df['PULocationID'].isin(allowed_ids) &
    ~df['DOLocationID'].isin(allowed_ids)
]

# Count flows PU → DO
flow_counts_ext = df_external.groupby(['PULocationID', 'DOLocationID']).size().reset_index(name='trip_count')

# Limit to top N flows
top_flows = flow_counts_ext.sort_values('trip_count', ascending=False).head(500)




# Load shapefile with zone geometries
zones = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones\taxi_zones.shp")
zones = zones[['LocationID', 'geometry']]
zones['centroid'] = zones.geometry.centroid
zones = zones.drop_duplicates(subset="LocationID")

# Merge centroid coordinates
zone_centroids = zones.set_index('LocationID')['centroid']
top_flows['PU_point'] = top_flows['PULocationID'].map(zone_centroids)
top_flows['DO_point'] = top_flows['DOLocationID'].map(zone_centroids)

# Drop missing centroids and create LineStrings
top_flows = top_flows.dropna(subset=['PU_point', 'DO_point'])
top_flows['line'] = top_flows.apply(lambda row: LineString([row['PU_point'], row['DO_point']]), axis=1)
flow_gdf = gpd.GeoDataFrame(top_flows, geometry='line')

# Normalize trip counts for width and color
max_count = flow_gdf['trip_count'].max()
flow_gdf['linewidth'] = flow_gdf['trip_count'] / max_count * 5 + 0.5

# Brighter color map and non-linear scaling for contrast
norm = PowerNorm(gamma=0.5, vmin=flow_gdf['trip_count'].min(), vmax=flow_gdf['trip_count'].max())
cmap = plt.cm.YlOrRd  # More dynamic range than Reds
flow_gdf['color'] = flow_gdf['trip_count'].apply(lambda x: cmap(norm(x)))


# Plot base map with blue background
fig, ax = plt.subplots(figsize=(14, 14))
zones.plot(ax=ax, facecolor='#cce5ff', edgecolor='#336699', linewidth=0.5)

# Draw colored flow lines
for _, row in flow_gdf.iterrows():
    ax.plot(*row['line'].xy, color=row['color'], linewidth=row['linewidth'], alpha=0.95)

plt.title("Top 500 NYC Taxi Flows (Brighter High-Volume Trips)", fontsize=16)
plt.axis('off')
plt.show()


