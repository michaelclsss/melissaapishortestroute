import pandas as pd
import numpy as np
from geopy.distance import geodesic

def build_distance_matrix(csv_path):
    # Load the CSV file with geocoded addresses
    df = pd.read_csv(csv_path)

    # Check required columns
    required_cols = {"RecordID", "Latitude", "Longitude"}
    if not required_cols.issubset(df.columns):
        raise ValueError("CSV must include: RecordID, Latitude, Longitude")

    # Prepare for distance matrix calculation
    n = len(df)
    distance_matrix = np.zeros((n, n))
    coords = list(zip(df["Latitude"], df["Longitude"]))
    record_ids = df["RecordID"].tolist()

    # Compute pairwise geodesic distances (in kilometers)
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = geodesic(coords[i], coords[j]).kilometers

    # Convert to DataFrame for display or export
    distance_df = pd.DataFrame(distance_matrix, index=record_ids, columns=record_ids)
    return distance_df

def construct_matrix():
    distance_df = build_distance_matrix("geocode.csv")
    print(distance_df.head())
    distance_df.to_csv("distance_matrix_km.csv") 