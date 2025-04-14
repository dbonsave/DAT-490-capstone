import pandas as pd
import geopandas as gpd

# Load GeoJSON with zone → borough mapping
zones = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones.geojson")[['LocationID', 'borough']]

# Function to standardize a dataset
def clean_and_standardize(df, pickup_col, dropoff_col, pu_col, do_col):
    df = df.dropna(subset=[pickup_col, dropoff_col, pu_col, do_col])
    df = df.rename(columns={
        pickup_col: 'Pickup Datetime',
        dropoff_col: 'Dropoff Datetime',
        pu_col: 'PULocationID',
        do_col: 'DOLocationID'
    })
    df = df[['Pickup Datetime', 'Dropoff Datetime', 'PULocationID', 'DOLocationID']]
    return df

# Load and clean Yellow
yellow = pd.read_parquet(r"C:\Users\David\Downloads\yellow_tripdata_2025-01 (1).parquet")
yellow = clean_and_standardize(yellow, 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID')

# Load and clean Green
green = pd.read_parquet(r"C:\Users\David\Downloads\green_tripdata_2025-01.parquet")
green = clean_and_standardize(green, 'lpep_pickup_datetime', 'lpep_dropoff_datetime', 'PULocationID', 'DOLocationID')

# Load and clean FHV
fhv = pd.read_parquet(r"C:\Users\David\Downloads\fhv_tripdata_2025-01.parquet")
fhv = clean_and_standardize(fhv, 'pickup_datetime', 'dropOff_datetime', 'PUlocationID', 'DOlocationID')

# Load and clean HVFHV (assuming path known already)
hvfhv = pd.read_parquet(r"C:\Users\David\Downloads\fhvhv_tripdata_2025-01.parquet")
hvfhv = clean_and_standardize(hvfhv, 'pickup_datetime', 'dropoff_datetime', 'PULocationID', 'DOLocationID')

# Combine all
combined = pd.concat([yellow, green, fhv, hvfhv], ignore_index=True)

# Join with borough info
combined = combined.merge(zones.rename(columns={'LocationID': 'PULocationID', 'borough': 'PU Borough'}), on='PULocationID', how='left')
combined = combined.merge(zones.rename(columns={'LocationID': 'DOLocationID', 'borough': 'DO Borough'}), on='DOLocationID', how='left')

# Export
combined.to_parquet(r"C:\Users\David\Downloads\AllTrips.parquet", index=False)
