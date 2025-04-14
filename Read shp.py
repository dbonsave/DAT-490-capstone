import geopandas as gpd
import matplotlib.pyplot as plt
# Load the shapefile
gdf = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones\taxi_zones.shp")

# Plot the map
gdf.plot(figsize=(10, 10), edgecolor='black')
plt.title("NYC Taxi Zones")
plt.show()


fig, ax = plt.subplots(figsize=(12, 12))
gdf.plot(ax=ax, edgecolor='black', facecolor='lightgray')

# Label each zone with its LocationID
for idx, row in gdf.iterrows():
    if row['geometry'].centroid.is_empty:
        continue
    plt.text(
        row['geometry'].centroid.x,
        row['geometry'].centroid.y,
        str(row['LocationID']),
        fontsize=8,
        ha='center',
        va='center'
    )

plt.title("NYC Taxi Zones with LocationIDs")
plt.axis('off')
plt.show()

