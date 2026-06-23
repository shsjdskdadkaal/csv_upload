#%%
import streamlit as st
import pandas as pd
import numpy as np


st.set_page_config(page_title="Battery City Screener", layout="wide")

st.title("🔋 Battery City Mismatch Screener")

# ==========================================================
# CITY CENTERS
# ==========================================================
city_centers = {
    "Ghaziabad": (28.6692, 77.4538),
    "Delhi": (28.6139, 77.2090),
    "Gurugram": (28.4595, 77.0266),
    "Jaipur": (26.9124, 75.7873),
    "Noida": (28.5355, 77.3910),
    "Bengaluru": (12.9716, 77.5946),
    "Faridabad": (28.4089, 77.3178),
    "Sonipat": (28.9931, 77.0151),
    "Panipat": (29.3909, 76.9635),
    "Vijayawada": (16.5062, 80.6480),
    "Mumbai": (19.0760, 72.8777),
    "Hyderabad": (17.3850, 78.4867),
    "Chandigarh": (30.7333, 76.7794),
    "Kochi": (9.9312, 76.2673),
    "Calicut": (11.2588, 75.7804),
    "Agra": (27.1767, 78.0081),
    "Pune": (18.5204, 73.8567),
    "Trivandrum": (8.5241, 76.9366),
    "Panchkula": (30.6942, 76.8606),
    "Chennai": (13.0827, 80.2707),
    "Mohali": (30.7046, 76.7179)
}

# ==========================================================
# CITY CLUSTERS
# ==========================================================
city_cluster = {

    "delhi": "ncr",
    "noida": "ncr",
    "ghaziabad": "ncr",
    "gurugram": "ncr",
    "faridabad": "ncr",
    "sonipat": "ncr",
    "panipat": "ncr",

    "chandigarh": "tricity",
    "mohali": "tricity",
    "panchkula": "tricity",

    "bengaluru": "bengaluru",
    "jaipur": "jaipur",
    "hyderabad": "hyderabad",
    "mumbai": "mumbai",
    "pune": "pune",
    "chennai": "chennai",
    "agra": "agra",
    "vijayawada": "vijayawada",
    "kochi": "kochi",
    "calicut": "calicut",
    "trivandrum": "trivandrum"
}


def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    lat1, lon1, lat2, lon2 = map(
        np.radians,
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def nearest_city(lat, lon):

    min_distance = float("inf")
    best_city = None

    for city, (city_lat, city_lon) in city_centers.items():

        distance = haversine(
            lat,
            lon,
            city_lat,
            city_lon
        )

        if distance < min_distance:
            min_distance = distance
            best_city = city

    return best_city


uploaded_file = st.file_uploader(
    "Upload AMD File",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    df = df[
        [
            'BP Serial Number',
            'Zone Name',
            'Last Latitude',
            'Last Longitude'
        ]
    ]

    # Invalid coordinates
    df['invalid_coordinate'] = (
        (df['Last Latitude'] < 6)
        | (df['Last Latitude'] > 38)
        | (df['Last Longitude'] < 68)
        | (df['Last Longitude'] > 98)
    )

    invalid_df = df[df['invalid_coordinate']].copy()

    valid_df = df[~df['invalid_coordinate']].copy()

    unique_coords = (
        valid_df[
            ['Last Latitude', 'Last Longitude']
        ]
        .drop_duplicates()
    )

    unique_coords['actual_city'] = unique_coords.apply(
        lambda x: nearest_city(
            x['Last Latitude'],
            x['Last Longitude']
        ),
        axis=1
    )

    valid_df = valid_df.merge(
        unique_coords,
        on=['Last Latitude', 'Last Longitude'],
        how='left'
    )

    valid_df['Zone Name'] = (
        valid_df['Zone Name']
        .str.lower()
        .str.strip()
    )

    valid_df['actual_city'] = (
        valid_df['actual_city']
        .str.lower()
        .str.strip()
    )

    valid_df['zone_cluster'] = (
        valid_df['Zone Name']
        .map(city_cluster)
    )

    valid_df['actual_cluster'] = (
        valid_df['actual_city']
        .map(city_cluster)
    )

    valid_df['city_mismatch'] = (
        valid_df['zone_cluster']
        != valid_df['actual_cluster']
    )

    risk_df = valid_df[
        valid_df['city_mismatch']
    ].copy()

    # KPIs
    c1, c2, c3 = st.columns(3)

    c1.metric("Total Batteries", len(df))
    c2.metric("Invalid Coordinates", len(invalid_df))
    c3.metric("City Mismatches", len(risk_df))

    st.subheader("City Mismatch Batteries")
    st.dataframe(risk_df)

    st.subheader("Invalid Coordinates")
    st.dataframe(invalid_df)

    st.download_button(
        "Download City Mismatch CSV",
        risk_df.to_csv(index=False),
        "battery_city_mismatch.csv",
        "text/csv"
    )

    st.download_button(
        "Download Invalid Coordinates CSV",
        invalid_df.to_csv(index=False),
        "invalid_coordinates.csv",
        "text/csv"
    )
