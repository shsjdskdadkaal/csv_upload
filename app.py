#%%
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import base64

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Indofast Asset Assurance Portal",
    page_icon="🔋",
    layout="wide"
)

# ==========================================================
# CUSTOM CSS
# ==========================================================
st.markdown("""
<style>
.main { background-color: #F0F2F6; }
h1, h2, h3 { color: #003B73; }

[data-testid="metric-container"] {
    background: white;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-left: 5px solid #003B73;
}

.stDownloadButton > button {
    background-color: #FF7A00;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.title("🔋 INDOFAST ASSET ASSURANCE PORTAL")

tab1, tab2 = st.tabs(["📍 Field Batteries", "🏭 Non Field Batteries"])

# ==========================================================
# CITY CENTERS
# ==========================================================
city_centers = {
    "Delhi":      (28.6139, 77.2090),
    "Ghaziabad":  (28.6692, 77.4538),
    "Noida":      (28.5355, 77.3910),
    "Gurugram":   (28.4595, 77.0266),
    "Faridabad":  (28.4089, 77.3178),
    "Sonipat":    (28.9931, 77.0151),
    "Panipat":    (29.3909, 76.9635),
    "Jaipur":     (26.9124, 75.7873),
    "Bengaluru":  (12.9716, 77.5946),
    "Hyderabad":  (17.3850, 78.4867),
    "Mumbai":     (19.0760, 72.8777),
    "Pune":       (18.5204, 73.8567),
    "Chennai":    (13.0827, 80.2707),
    "Agra":       (27.1767, 78.0081),
    "Vijayawada": (16.5062, 80.6480),
    "Chandigarh": (30.7333, 76.7794),
    "Mohali":     (30.7046, 76.7179),
    "Panchkula":  (30.6942, 76.8606),
    "Kochi":      (9.9312,  76.2673),
    "Calicut":    (11.2588, 75.7804),
    "Trivandrum": (8.5241,  76.9366),
    "Ahmedabad":  (23.0225, 72.5714),
    "Kolkata":    (22.5726, 88.3639)
}

# ==========================================================
# HELPERS
# ==========================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

def nearest_city_with_dist(lat, lon):
    min_dist, best = float("inf"), None
    for city, (clat, clon) in city_centers.items():
        d = haversine(lat, lon, clat, clon)
        if d < min_dist:
            min_dist, best = d, city
    return best, round(min_dist, 2)

def dist_to_assigned_city(lat, lon, city_name):
    key = city_name.title()
    coords = city_centers.get(key)
    if coords is None:
        for k, v in city_centers.items():
            if k.lower() == key.lower():
                coords = v; break
    if coords is None:
        return None
    return round(haversine(lat, lon, coords[0], coords[1]), 2)

# ==========================================================
# HEATMAP — polished look, always-dark text
# ==========================================================
def build_heatmap(pivot_df, x_col, y_col, z_col, title, colorscale):
    x_vals = sorted(pivot_df[x_col].unique())
    y_vals = sorted(pivot_df[y_col].unique())

    z_matrix, text_matrix = [], []
    all_vals = []
    for y in y_vals:
        row, text_row = [], []
        for x in x_vals:
            m = pivot_df[(pivot_df[x_col]==x) & (pivot_df[y_col]==y)]
            val = int(m[z_col].values[0]) if len(m) > 0 else 0
            row.append(val if val > 0 else None)
            text_row.append(str(val) if val > 0 else "")
            if val > 0:
                all_vals.append(val)
        z_matrix.append(row)
        text_matrix.append(text_row)

    max_val = max(all_vals) if all_vals else 1
    height  = max(560, 80 + len(y_vals) * 42)
    l_margin = max(140, max(len(str(v)) for v in y_vals) * 9 + 30)

    threshold = max_val * 0.55

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        x=x_vals, y=y_vals, z=z_matrix,
        colorscale=colorscale,
        showscale=True,
        zmin=0, zmax=max_val,
        colorbar=dict(
            title=dict(text="Count", font=dict(size=12)),
            thickness=16, len=0.75,
            tickfont=dict(size=11)
        ),
        hovertemplate="<b>Zone:</b> %{y}<br><b>Actual:</b> %{x}<br><b>Batteries:</b> %{z}<extra></extra>"
    ))

    annotations = []
    for yi, y in enumerate(y_vals):
        for xi, x in enumerate(x_vals):
            m = pivot_df[(pivot_df[x_col]==x) & (pivot_df[y_col]==y)]
            val = int(m[z_col].values[0]) if len(m) > 0 else 0
            if val == 0:
                continue
            text_color = "white" if val > threshold else "#1a1a2e"
            annotations.append(dict(
                x=x, y=y,
                text=f"<b>{val:,}</b>",
                showarrow=False,
                font=dict(size=11, color=text_color),
                xref="x", yref="y"
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#003B73"), x=0.01),
        height=height,
        margin=dict(l=l_margin, r=90, t=65, b=140),
        annotations=annotations,
        xaxis=dict(
            title=dict(text="Actual City (GPS)", font=dict(size=13, color="#444"), standoff=18),
            tickangle=-42,
            tickfont=dict(size=11, color="#333"),
            side="bottom",
            showgrid=False,
            linecolor="#ccc", linewidth=1
        ),
        yaxis=dict(
            title=dict(text="Expected / Zone City", font=dict(size=13, color="#444"), standoff=12),
            tickfont=dict(size=11, color="#333"),
            automargin=True,
            showgrid=False,
            linecolor="#ccc", linewidth=1
        ),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif")
    )
    return fig

# ==========================================================
# SHARE HTML
# ==========================================================
def share_html(fig, filename_prefix):
    html_str  = pio.to_html(fig, full_html=True, include_plotlyjs="cdn")
    b64_html  = base64.b64encode(html_str.encode()).decode()
    st.markdown(
        f'<a href="data:text/html;base64,{b64_html}" '
        f'download="{filename_prefix}.html" '
        f'style="display:inline-block;padding:9px 20px;background:#FF7A00;color:white;'
        f'border-radius:8px;text-decoration:none;font-weight:600;font-size:13px;">'
        f'🌐 Download & Share (Interactive HTML)</a>',
        unsafe_allow_html=True
    )
    st.caption("Opens in any browser · hover to explore · attach to email or upload to Drive")

# ==========================================================
# NON FIELD MAPPINGS
# ==========================================================
non_field_mapping = {
    "delhi - non field":"delhi","delhi - wh":"delhi",
    "ghaziabad - non field":"ghaziabad","noida - non field":"noida",
    "gurugram - non field":"gurugram","gurugram - wh":"gurugram",
    "faridabad - non field":"faridabad","sonipat - non field":"sonipat",
    "panipat - non field":"panipat",
    "smpl elrc dl":"delhi","inward store elrc - delhi":"delhi",
    "jaipur - wh":"jaipur","jaipur - non field":"jaipur","bhiwadi - non field":"jaipur",
    "bengaluru - wh":"bengaluru","bengaluru - non field":"bengaluru","smpl elrc ka":"bengaluru",
    "hyderabad - wh":"hyderabad","hyderabad - non field":"hyderabad",
    "pune - wh":"pune","pune - non field":"pune","baramati":"pune",
    "chennai - wh":"chennai","chennai - non field":"chennai",
    "ranipet - non field":"chennai","tamil nadu - non field":"chennai",
    "mumbai - wh":"mumbai","mumbai - non field":"mumbai",
    "chandigarh - wh":"chandigarh","chandigarh - non field":"chandigarh",
    "sanand - non field":"ahmedabad",
    "agra - non field":"agra","vijayawada - non field":"vijayawada",
    "kolkata - non field":"kolkata","kolkata":"kolkata"
}

exclude_zones = [
    "testing","oem","scrapped","fir raised","pdi clearance",
    "to be written off","quarantine elrc","invoiced to isepl","sm-stores"
]

hub_city_keywords = [
    "delhi","ghaziabad","noida","gurugram","faridabad","sonipat","panipat",
    "jaipur","bengaluru","hyderabad","mumbai","pune","chennai",
    "agra","vijayawada","kolkata","ahmedabad"
]

def get_expected_city(row):
    zone    = str(row['Zone Name']).strip().lower()
    subzone = str(row['Subzone Name']).strip().lower()
    if zone == "hubs":
        for city in hub_city_keywords:
            if city in subzone:
                return city
        return None
    return non_field_mapping.get(zone)

# ==========================================================
# KPI CARD ROW — 5-metric row
# ==========================================================
def kpi_row(total, diff_city_count, over50_count, invalid_count):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔋 Total BPs",               f"{total:,}")
    c2.metric("🔄 Different City",           f"{diff_city_count:,}",
              help="Batteries whose nearest city differs from their assigned zone city")
    c3.metric("🚨 >50 km from Nearest City", f"{over50_count:,}",
              help="Batteries that are >50 km away from their nearest city center")
    c4.metric("📡 Invalid Coordinates",      f"{invalid_count:,}")

# ==========================================================
# FIELD BATTERY TAB
# ==========================================================
with tab1:
    st.header("Field Battery Location Screener")
    uploaded_field = st.file_uploader("Upload Field Battery CSV", type=["csv"], key="field_file")

    if uploaded_field:
        df = pd.read_csv(uploaded_field)
        df = df[[
            'BP Serial Number','Zone Name','Zone Subzone Type',
            'Last Latitude','Last Longitude',
            'Last TIU Time','Current Atom Zone Transfer Datetime'
        ]]

        df['Last TIU Time'] = pd.to_datetime(df['Last TIU Time'], errors='coerce')
        df['Current Atom Zone Transfer Datetime'] = pd.to_datetime(
            df['Current Atom Zone Transfer Datetime'], errors='coerce')

        df['check_location'] = df['Last TIU Time'] > df['Current Atom Zone Transfer Datetime']

        df['invalid_coordinate'] = (
            (df['Last Latitude']  < 6)  | (df['Last Latitude']  > 38) |
            (df['Last Longitude'] < 68) | (df['Last Longitude'] > 98)
        )

        invalid_df = df[df['invalid_coordinate']].copy()
        valid_df   = df[(~df['invalid_coordinate']) & df['check_location']].copy()

        # ── Nearest city + distance to nearest city center ────
        uc = valid_df[['Last Latitude','Last Longitude']].drop_duplicates().copy()
        res = uc.apply(
            lambda r: nearest_city_with_dist(r['Last Latitude'], r['Last Longitude']), axis=1)
        uc['actual_city']              = res.apply(lambda x: x[0])
        uc['dist_to_nearest_city_km']  = res.apply(lambda x: x[1])   # ← renamed
        valid_df = valid_df.merge(uc, on=['Last Latitude','Last Longitude'], how='left')

        valid_df['Zone Name']   = valid_df['Zone Name'].astype(str).str.strip().str.lower()
        valid_df['actual_city'] = valid_df['actual_city'].astype(str).str.strip().str.lower()

        # ── Flag: zone city ≠ nearest city ───────────────────
        valid_df['diff_city'] = valid_df['Zone Name'] != valid_df['actual_city']

        # ── Flag: distance to nearest city center > 50 km ────
        valid_df['dist_gt_50'] = valid_df['dist_to_nearest_city_km'] > 50   # ← new column

        # Mismatch subset: different city only (all mismatches)
        diff_city_df = valid_df[valid_df['diff_city']].copy()

        # Risk subset: different city AND >50 km from nearest city
        risk_df = valid_df[valid_df['diff_city'] & valid_df['dist_gt_50']].copy()

        # ── KPI Row ───────────────────────────────────────────
        kpi_row(len(df), len(diff_city_df), len(risk_df), len(invalid_df))

        st.divider()

        # ── All Different City Table (≤50 km and >50 km) ─────
        st.subheader("⚠️ Field Battery Mismatch Table  (all different-city batteries)")
        st.caption("Shows every battery where zone city ≠ nearest city · `Dist > 50 km` column flags the higher-risk ones")
        st.dataframe(
            diff_city_df[[
                'BP Serial Number','Zone Subzone Type','Zone Name',
                'Last Latitude','Last Longitude',
                'Last TIU Time','Current Atom Zone Transfer Datetime',
                'actual_city','dist_to_nearest_city_km','dist_gt_50'
            ]].rename(columns={
                'actual_city':             'Nearest City (GPS)',
                'dist_to_nearest_city_km': 'Dist to Nearest City (km)',
                'dist_gt_50':              'Dist > 50 km'
            }),
            use_container_width=True
        )

        st.divider()

        # ── Heatmap — all different-city (both ≤50 and >50 km) ─
        st.subheader("🔥 Zone City vs Actual City Heatmap  (all mismatches)")
        st.caption("Cells show batteries assigned to Zone City (Y-axis) but found in Nearest City (X-axis) — includes all different-city batteries")

        hm_f = diff_city_df.groupby(['Zone Name','actual_city']).size().reset_index(name='Battery Count')
        if len(hm_f) > 0:
            fig_fh = build_heatmap(hm_f,'actual_city','Zone Name','Battery Count',
                                   'Field Batteries — Zone City (Y) vs Actual GPS City (X)','Blues')
            st.plotly_chart(fig_fh, use_container_width=True)
            share_html(fig_fh, "field_zone_vs_actual_heatmap")

        st.divider()

        # ── Top Cities side-by-side ───────────────────────────
        st.subheader("📊 Top Mismatch Cities")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Zone Cities Losing Batteries**")
            tz = diff_city_df['Zone Name'].value_counts().head(10).reset_index()
            tz.columns = ['City','Count']
            fig_tz = px.bar(tz, x='Count', y='City', orientation='h',
                            color='Count', color_continuous_scale='Blues')
            fig_tz.update_layout(showlegend=False, coloraxis_showscale=False,
                                 yaxis=dict(autorange='reversed', automargin=True),
                                 margin=dict(l=10,r=10,t=20,b=10), height=360)
            st.plotly_chart(fig_tz, use_container_width=True)
        with cb:
            st.markdown("**Cities Absorbing Batteries**")
            ta = diff_city_df['actual_city'].value_counts().head(10).reset_index()
            ta.columns = ['City','Count']
            fig_ta = px.bar(ta, x='Count', y='City', orientation='h',
                            color='Count', color_continuous_scale='Oranges')
            fig_ta.update_layout(showlegend=False, coloraxis_showscale=False,
                                 yaxis=dict(autorange='reversed', automargin=True),
                                 margin=dict(l=10,r=10,t=20,b=10), height=360)
            st.plotly_chart(fig_ta, use_container_width=True)

        st.divider()
        st.download_button("Download Field Mismatch CSV",
                           diff_city_df.to_csv(index=False), "field_mismatch.csv")


# ==========================================================
# NON FIELD TAB
# ==========================================================
with tab2:
    st.header("Non Field Battery Location Screener")
    uploaded_non_field = st.file_uploader("Upload Non Field Battery CSV", type=["csv"], key="non_field_file")

    if uploaded_non_field:
        nf = pd.read_csv(uploaded_non_field)
        nf = nf[[
            'BP Serial Number','Zone Name','Subzone Name','Zone Subzone Type',
            'Last Latitude','Last Longitude',
            'Last TIU Time','Current Atom Zone Transfer Datetime'
        ]]

        nf['Zone Name'] = nf['Zone Name'].astype(str).str.strip().str.lower()
        nf = nf[~nf['Zone Name'].isin(exclude_zones)].copy()

        nf['Last TIU Time'] = pd.to_datetime(nf['Last TIU Time'], errors='coerce')
        nf['Current Atom Zone Transfer Datetime'] = pd.to_datetime(
            nf['Current Atom Zone Transfer Datetime'], errors='coerce')

        nf['check_location'] = nf['Last TIU Time'] > nf['Current Atom Zone Transfer Datetime']

        nf['invalid_coordinate'] = (
            (nf['Last Latitude']  < 6)  | (nf['Last Latitude']  > 38) |
            (nf['Last Longitude'] < 68) | (nf['Last Longitude'] > 98)
        )

        invalid_nf = nf[nf['invalid_coordinate']].copy()
        valid_nf   = nf[(~nf['invalid_coordinate']) & nf['check_location']].copy()

        # ── Nearest city + distance to nearest city center ────
        uc_nf = valid_nf[['Last Latitude','Last Longitude']].drop_duplicates().copy()
        res_nf = uc_nf.apply(
            lambda r: nearest_city_with_dist(r['Last Latitude'], r['Last Longitude']), axis=1)
        uc_nf['actual_city']             = res_nf.apply(lambda x: x[0])
        uc_nf['dist_to_nearest_city_km'] = res_nf.apply(lambda x: x[1])   # ← renamed
        valid_nf = valid_nf.merge(uc_nf, on=['Last Latitude','Last Longitude'], how='left')
        valid_nf['actual_city'] = valid_nf['actual_city'].astype(str).str.strip().str.lower()

        # Expected city
        valid_nf['expected_city'] = valid_nf.apply(get_expected_city, axis=1)
        valid_nf = valid_nf[valid_nf['expected_city'].notna()].copy()

        # ── Flag: expected city ≠ nearest city ───────────────
        valid_nf['diff_city'] = valid_nf['expected_city'] != valid_nf['actual_city']

        # ── Flag: distance to nearest city center > 50 km ────
        valid_nf['dist_gt_50'] = valid_nf['dist_to_nearest_city_km'] > 50   # ← new column

        # Mismatch subset
        diff_city_nf = valid_nf[valid_nf['diff_city']].copy()

        # Risk subset: different city AND >50 km from nearest city
        risk_nf = valid_nf[valid_nf['diff_city'] & valid_nf['dist_gt_50']].copy()
        risk_nf.to_csv("non_field_mismatch_latest.csv", index=False)

        # ── KPI Row ───────────────────────────────────────────
        kpi_row(len(nf), len(diff_city_nf), len(risk_nf), len(invalid_nf))

        st.divider()

        # ── All Different City Table (≤50 km and >50 km) ─────
        st.subheader("⚠️ Non Field Battery Mismatch Table  (all different-city batteries)")
        st.caption("Shows every battery where expected city ≠ nearest city · `Dist > 50 km` column flags the higher-risk ones")
        st.dataframe(
            diff_city_nf[[
                'BP Serial Number','Zone Name','Subzone Name',
                'Last Latitude','Last Longitude',
                'expected_city','actual_city',
                'dist_to_nearest_city_km','dist_gt_50'
            ]].rename(columns={
                'actual_city':             'Nearest City (GPS)',
                'expected_city':           'Expected City (Zone)',
                'dist_to_nearest_city_km': 'Dist to Nearest City (km)',
                'dist_gt_50':              'Dist > 50 km'
            }),
            use_container_width=True
        )

        st.divider()

        # ── Heatmap — all different-city (both ≤50 and >50 km) ─
        st.subheader("🔥 Zone City vs Actual City Heatmap  (all mismatches)")
        st.caption("Cells show batteries assigned to Expected City (Y-axis) but found in Nearest City (X-axis) — includes all different-city batteries")

        hm_nf = diff_city_nf.groupby(['expected_city','actual_city']).size().reset_index(name='Battery Count')
        if len(hm_nf) > 0:
            fig_heat = build_heatmap(hm_nf,'actual_city','expected_city','Battery Count',
                                     'Non-Field Batteries — Expected City (Y) vs Actual GPS City (X)','YlOrRd')
            st.plotly_chart(fig_heat, use_container_width=True)
            share_html(fig_heat, "nonfield_zone_vs_actual_heatmap")

        st.divider()

        # ── Top Cities ────────────────────────────────────────
        st.subheader("📊 Top Mismatch Cities")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Zone Cities Losing Batteries**")
            te = diff_city_nf['expected_city'].value_counts().head(10).reset_index()
            te.columns = ['City','Count']
            fig_te = px.bar(te, x='Count', y='City', orientation='h',
                            color='Count', color_continuous_scale='Oranges')
            fig_te.update_layout(showlegend=False, coloraxis_showscale=False,
                                 yaxis=dict(autorange='reversed', automargin=True),
                                 margin=dict(l=10,r=10,t=20,b=10), height=360)
            st.plotly_chart(fig_te, use_container_width=True)
        with cb:
            st.markdown("**Cities Absorbing Batteries**")
            ta2 = diff_city_nf['actual_city'].value_counts().head(10).reset_index()
            ta2.columns = ['City','Count']
            fig_ta2 = px.bar(ta2, x='Count', y='City', orientation='h',
                             color='Count', color_continuous_scale='Reds')
            fig_ta2.update_layout(showlegend=False, coloraxis_showscale=False,
                                  yaxis=dict(autorange='reversed', automargin=True),
                                  margin=dict(l=10,r=10,t=20,b=10), height=360)
            st.plotly_chart(fig_ta2, use_container_width=True)

        st.divider()

        # ── Sankey ────────────────────────────────────────────
        st.subheader("🔀 Battery Migration Flow (Sankey)")
        st.caption("Width = number of batteries moving between cities")

        flow = (diff_city_nf.groupby(['expected_city','actual_city'])
                .size().reset_index(name='count')
                .sort_values('count', ascending=False).head(30))

        if len(flow) > 0:
            all_nodes = list(pd.unique(flow[['expected_city','actual_city']].values.ravel()))
            node_idx  = {n: i for i, n in enumerate(all_nodes)}
            fig_sankey = go.Figure(go.Sankey(
                node=dict(pad=18, thickness=22,
                          line=dict(color="#ccc", width=0.5),
                          label=all_nodes,
                          color=["#003B73" if n in flow['expected_city'].values else "#FF7A00"
                                 for n in all_nodes]),
                link=dict(
                    source=[node_idx[r] for r in flow['expected_city']],
                    target=[node_idx[r] for r in flow['actual_city']],
                    value=flow['count'].tolist(),
                    color="rgba(255,122,0,0.22)")
            ))
            fig_sankey.update_layout(
                title="Battery Flow: Expected City → Actual City",
                height=520, margin=dict(l=20,r=20,t=50,b=20))
            st.plotly_chart(fig_sankey, use_container_width=True)
            share_html(fig_sankey, "nonfield_battery_flow_sankey")

        st.divider()

        st.download_button("Download Non Field Mismatch CSV",
                           diff_city_nf.to_csv(index=False), "non_field_mismatch.csv")
        st.download_button("Download Invalid Coordinate CSV",
                           invalid_nf.to_csv(index=False), "non_field_invalid_coordinates.csv")
