import geopandas as gpd

# Load the original shapefile
zones = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones\taxi_zones.shp")

# Reproject to EPSG:4326 (lat/lng)
zones = zones.to_crs(epsg=4326)

# Export to GeoJSON
zones.to_file(r"C:\Users\David\Downloads\taxi_zones.geojson", driver='GeoJSON')
