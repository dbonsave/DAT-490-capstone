import pandas as pd
import geopandas as gpd

# Load GeoJSON with borough info
zones = gpd.read_file(r"C:\Users\David\Downloads\taxi_zones.geojson")[['LocationID', 'borough']]

# Function to standardize and tag vendor with a fare column
def clean(df, pickup_col, dropoff_col, pu_col, do_col, vendor_name, fare_cols=None):
    df = df.dropna(subset=[pickup_col, dropoff_col, pu_col, do_col])
    df = df.rename(columns={
        pickup_col: 'Pickup Datetime',
        dropoff_col: 'Dropoff Datetime',
        pu_col: 'PULocationID',
        do_col: 'DOLocationID'
    })
    df['Vendor'] = vendor_name
    if fare_cols:
        df['fare'] = df.reindex(columns=fare_cols, fill_value=0).sum(axis=1)
    else:
        df['fare'] = None
    return df[['Pickup Datetime', 'Dropoff Datetime', 'PULocationID', 'DOLocationID', 'Vendor', 'fare']]

# Yellow Taxi
yellow = pd.read_parquet(r"C:\Users\David\Downloads\yellow_tripdata_2025-01 (1).parquet")
yellow_fare_cols = [
    'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
    'improvement_surcharge', 'congestion_surcharge', 'airport_fee', 'cbd_congestion_fee'
]
yellow = clean(yellow, 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'Yellow Taxi', yellow_fare_cols)

# Green Taxi
green = pd.read_parquet(r"C:\Users\David\Downloads\green_tripdata_2025-01.parquet")
green_fare_cols = [
    'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
    'improvement_surcharge', 'congestion_surcharge', 'cbd_congestion_fee'
]
green = clean(green, 'lpep_pickup_datetime', 'lpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'Green Taxi', green_fare_cols)

# For Hire Vehicle (individual)
fhv = pd.read_parquet(r"C:\Users\David\Downloads\fhv_tripdata_2025-01.parquet")
fhv = clean(fhv, 'pickup_datetime', 'dropOff_datetime', 'PUlocationID', 'DOlocationID', 'For Hire vehicle (individual)')

# HVFHV (Uber/Lyft/etc.)
hvfhv = pd.read_parquet(r"C:\Users\David\Downloads\fhvhv_tripdata_2025-01.parquet")
hvfhv = hvfhv.dropna(subset=['pickup_datetime', 'dropoff_datetime', 'PULocationID', 'DOLocationID'])
hvfhv = hvfhv.rename(columns={
    'pickup_datetime': 'Pickup Datetime',
    'dropoff_datetime': 'Dropoff Datetime'
})
hvfhv['Vendor'] = hvfhv['hvfhs_license_num'].map({
    'HV0002': 'Juno',
    'HV0003': 'Uber',
    'HV0004': 'Via',
    'HV0005': 'Lyft'
})
hvfhv_fare_cols = [
    'base_passenger_fare', 'bcf', 'sales_tax', 'congestion_surcharge',
    'airport_fee', 'tips', 'cbd_congestion_fee'
]
hvfhv['fare'] = hvfhv.reindex(columns=hvfhv_fare_cols, fill_value=0).sum(axis=1)
hvfhv = hvfhv[['Pickup Datetime', 'Dropoff Datetime', 'PULocationID', 'DOLocationID', 'Vendor', 'fare']]

# Combine all datasets
combined = pd.concat([yellow, green, fhv, hvfhv], ignore_index=True)

# Map boroughs
combined = combined.merge(zones.rename(columns={'LocationID': 'PULocationID', 'borough': 'PU Borough'}), on='PULocationID', how='left')
combined = combined.merge(zones.rename(columns={'LocationID': 'DOLocationID', 'borough': 'DO Borough'}), on='DOLocationID', how='left')

# Export
combined.to_parquet(r"C:\Users\David\Downloads\AllTrips2.parquet", index=False)
