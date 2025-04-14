import pandas as pd
import geopandas as gpd

# Load trip data
df = pd.read_parquet(r"C:\Users\David\Downloads\alltrips2.parquet")

# Filter to only trips starting OR ending in the Bronx
df_filtered = df[
    (df['PU Borough'] == 'Bronx') | (df['DO Borough'] == 'Bronx')
].copy()

# Read and project taxi zone shapefile
zones = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones\taxi_zones.shp")
zones = zones.to_crs(epsg=2263)
zones['centroid'] = zones.geometry.centroid
zones = zones.drop_duplicates(subset="LocationID")
zones['centroid'] = zones['centroid'].to_crs(epsg=4326)
centroids = zones.set_index('LocationID')['centroid']

# Group by PU, DO, and Vendor to count trips
grouped = df_filtered.groupby(['PULocationID', 'DOLocationID', 'Vendor', 'PU Borough', 'DO Borough']) \
                     .size().reset_index(name='trip_count')

# Add coordinates from centroids
grouped['origin_point'] = grouped['PULocationID'].map(centroids)
grouped['dest_point'] = grouped['DOLocationID'].map(centroids)

# Drop rows where mapping failed
grouped = grouped.dropna(subset=['origin_point', 'dest_point'])

# Extract lat/lng
grouped['origin_lat'] = grouped['origin_point'].apply(lambda p: p.y)
grouped['origin_lng'] = grouped['origin_point'].apply(lambda p: p.x)
grouped['dest_lat'] = grouped['dest_point'].apply(lambda p: p.y)
grouped['dest_lng'] = grouped['dest_point'].apply(lambda p: p.x)

# Select export columns
columns_to_export = [
    'PULocationID', 'DOLocationID',
    'Vendor', 'trip_count',
    'PU Borough', 'DO Borough',
    'origin_lat', 'origin_lng', 'dest_lat', 'dest_lng'
]

# Export to CSV
grouped[columns_to_export].to_csv("C:/Users/David/Downloads/taxi_flow_kepler_bronx_totals_better.csv", index=False)
