#%%
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Indofast Asset Assurance",
    page_icon="🔋",
    layout="wide"
)

st.markdown("""
<style>

.main {
    background-color: #F5F7FA;
}

h1,h2,h3 {
    color: #003B73;
}

[data-testid="metric-container"]{
    background-color:white;
    border-radius:15px;
    padding:20px;
    box-shadow:0px 2px 10px rgba(0,0,0,0.08);
}

.stDownloadButton > button{
    background-color:#FF7A00;
    color:white;
    border:none;
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)

st.title("🔋 INDOFAST ASSET ASSURANCE PORTAL")

tab1, tab2 = st.tabs(
    [
        "Field Batteries",
        "Non Field Batteries"
    ]
)

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
    "Mohali": (30.7046, 76.7179),
    "Ahmedabad": (23.0225,72.5714),
    "Kolkata": (22.5726,88.3639)
}

city_cluster = {

    # NCR
    "delhi":"ncr",
    "noida":"ncr",
    "ghaziabad":"ncr",
    "gurugram":"ncr",
    "faridabad":"ncr",
    "sonipat":"ncr",
    "panipat":"ncr",

    # Tricity
    "chandigarh":"tricity",
    "mohali":"tricity",
    "panchkula":"tricity",

    # Kerala
    "kochi":"kerala",
    "calicut":"kerala",
    "trivandrum":"kerala",

    "bengaluru":"bengaluru",
    "jaipur":"jaipur",
    "hyderabad":"hyderabad",
    "mumbai":"mumbai",
    "pune":"pune",
    "chennai":"chennai",
    "agra":"agra",
    "vijayawada":"vijayawada",
    "ahmedabad":"ahmedabad",
    "kolkata":"kolkata"
}
# ==========================================================
# FUNCTIONS
# ==========================================================
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


# ==========================================================
# FIELD BATTERIES TAB
# ==========================================================
with tab1:

    st.header("Field Battery Location Screener")

    uploaded_field = st.file_uploader(
        "Upload Field Battery CSV",
        type=["csv"],
        key="field"
    )

    if uploaded_field:

        df = pd.read_csv(uploaded_field)

        df = df[
            [
                'BP Serial Number',
                'Zone Name',
                'Last Latitude',
                'Last Longitude',
                'Zone Subzone Type'
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

        # Unique coordinates
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
            !=
            valid_df['actual_cluster']
        )

        risk_df = valid_df[
            valid_df['city_mismatch']
        ].copy()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🔋 Total Batteries",
            len(df)
        )

        c2.metric(
            "📡 Invalid Coordinates",
            len(invalid_df)
        )

        c3.metric(
            "⚠️ City Mismatch",
            len(risk_df)
        )

        st.subheader("City Mismatch Batteries")

        st.dataframe(
    risk_df[
        [
            'BP Serial Number',
            'Zone Subzone Type',
            'Zone Name',
            'Last Latitude',
            'Last Longitude',
            'actual_city',
            'zone_cluster',
            'actual_cluster'
        ]
    ],
    use_container_width=True
)

        st.subheader("Invalid Coordinates")

        st.dataframe(
            invalid_df,
            use_container_width=True
        )

        st.download_button(
            "Download Field Mismatch CSV",
            risk_df.to_csv(index=False),
            "field_battery_mismatch.csv"
        )

        st.download_button(
            "Download Invalid Coordinates CSV",
            invalid_df.to_csv(index=False),
            "invalid_coordinates.csv"
        )

# ==========================================================
# NON FIELD ZONE NORMALIZATION
# ==========================================================
non_field_mapping = {

    # NCR
    "Delhi - Non field": "ncr",
    "Delhi - WH": "ncr",
    "Ghaziabad - Non field": "ncr",
    "Noida - Non field": "ncr",
    "Gurugram - Non field": "ncr",
    "Gurugram - WH": "ncr",
    "Faridabad - Non field": "ncr",
    "Sonipat - Non field": "ncr",
    "Panipat - Non Field": "ncr",
    "SMPL ELRC DL": "ncr",
    "Inward Store ELRC - Delhi": "ncr",

    # Jaipur
    "Jaipur - WH": "jaipur",
    "Jaipur - Non Field": "jaipur",
    "Bhiwadi - Non field": "jaipur",

    # Bengaluru
    "Bengaluru - WH": "bengaluru",
    "Bengaluru - Non field": "bengaluru",
    "SMPL ELRC KA": "bengaluru",

    # Hyderabad
    "Hyderabad - Non field": "hyderabad",
    "Hyderabad - WH": "hyderabad",

    # Pune
    "Pune - WH": "pune",
    "Pune - Non field": "pune",
    "Baramati": "pune",

    # Chennai
    "Chennai - WH": "chennai",
    "Chennai - Non Field": "chennai",
    "Tamil Nadu - Non Field": "chennai",
    "Ranipet - Non Field": "chennai",

    # Mumbai
    "Mumbai - Non field": "mumbai",
    "Mumbai - WH": "mumbai",

    # Tricity
    "Chandigarh - Non field": "tricity",
    "Chandigarh - WH": "tricity",

    # Ahmedabad
    "Sanand - Non Field": "ahmedabad",

    # Standalone
    "Agra - Non Field": "agra",
    "Vijayawada - Non Field": "vijayawada",
    "Kolkata - Non field": "kolkata",
    "Kolkata": "kolkata"
}


exclude_zones = [
    "Testing",
    "OEM",
    "Scrapped",
    "FIR Raised",
    "PDI Clearance",
    "To be written off",
    "Quarantine ELRC",
    "Invoiced to ISEPL",
    "Hubs",
    "SM-Stores"
]


# ==========================================================
# NON FIELD TAB
# ==========================================================
with tab2:

    st.header("Non Field Battery Location Screener")

    uploaded_non_field = st.file_uploader(
        "Upload Non Field CSV",
        type=["csv"],
        key="non_field"
    )

    if uploaded_non_field:

        nf = pd.read_csv(uploaded_non_field)

        nf = nf[
            [
                'BP Serial Number',
                'Zone Name',
                'Last Latitude',
                'Last Longitude',
                'Zone Subzone Type'
            ]
        ]

        # Remove excluded zones
        nf = nf[
            ~nf['Zone Name'].isin(exclude_zones)
        ].copy()

        # Invalid coordinates
        nf['invalid_coordinate'] = (
            (nf['Last Latitude'] < 6)
            | (nf['Last Latitude'] > 38)
            | (nf['Last Longitude'] < 68)
            | (nf['Last Longitude'] > 98)
        )

        invalid_nf = nf[nf['invalid_coordinate']].copy()

        valid_nf = nf[~nf['invalid_coordinate']].copy()

        unique_coords_nf = (
            valid_nf[
                ['Last Latitude', 'Last Longitude']
            ]
            .drop_duplicates()
        )

        unique_coords_nf['actual_city'] = unique_coords_nf.apply(
            lambda x: nearest_city(
                x['Last Latitude'],
                x['Last Longitude']
            ),
            axis=1
        )

        valid_nf = valid_nf.merge(
            unique_coords_nf,
            on=['Last Latitude', 'Last Longitude'],
            how='left'
        )

        valid_nf['actual_city'] = (
            valid_nf['actual_city']
            .str.lower()
            .str.strip()
        )

        valid_nf['zone_cluster'] = (
            valid_nf['Zone Name']
            .map(non_field_mapping)
        )

        valid_nf['actual_cluster'] = (
            valid_nf['actual_city']
            .map(city_cluster)
        )

        valid_nf['city_mismatch'] = (
            valid_nf['zone_cluster']
            !=
            valid_nf['actual_cluster']
        )

        risk_nf = valid_nf[
            valid_nf['city_mismatch']
        ].copy()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🔋 Total Batteries",
            len(nf)
        )

        c2.metric(
            "📡 Invalid Coordinates",
            len(invalid_nf)
        )

        c3.metric(
            "⚠️ Non Field Mismatch",
            len(risk_nf)
        )

        st.subheader("Non Field Mismatch Batteries")

        st.dataframe(
            risk_nf[
                [
                    'BP Serial Number',
                    'Zone Subzone Type',
                    'Zone Name',
                    'Last Latitude',
                    'Last Longitude',
                    'actual_city',
                    'zone_cluster',
                    'actual_cluster'
                ]
            ],
            use_container_width=True
        )

        st.subheader("Invalid Coordinates")

        st.dataframe(
            invalid_nf,
            use_container_width=True
        )

        st.download_button(
            "Download Non Field Mismatch CSV",
            risk_nf.to_csv(index=False),
            "non_field_mismatch.csv"
        )

        st.download_button(
            "Download Invalid Coordinates CSV",
            invalid_nf.to_csv(index=False),
            "invalid_non_field_coordinates.csv"
        )
