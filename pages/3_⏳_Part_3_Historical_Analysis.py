import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Part 3: Historical Analysis (1931-2008)",
    page_icon="⏳",
    layout="wide"
)

st.title("⏳ Part 3: Historical Mortality Analysis (1931–2008)")
st.markdown("Reconstruction of historical mortality trends and spatial patterns in Türkiye.")


# -----------------------------------------------------------------------------
# 2. SHARED DATA LOADING FUNCTIONS
# -----------------------------------------------------------------------------

@st.cache_data
def load_trend_data():
    """Loads and merges Province (1931-2008) and Region (1972-2008) qx data."""
    # 1. Load Province Data
    path_prov = os.path.join("data", "part3_prov_qx.xlsx")
    try:
        df_prov = pd.read_excel(path_prov)
    except Exception as e:
        st.error(f"Error loading province data: {e}")
        return pd.DataFrame()

    # 2. Load Region Data
    path_reg = os.path.join("data", "part3_region_qx.xlsx")
    try:
        df_reg = pd.read_excel(path_reg)
        # Rename columns to match structure
        df_reg = df_reg.rename(columns={'upper_age': 'rate', 'p_qx': 'qx'})
    except Exception as e:
        st.error(f"Error loading region data: {e}")
        return pd.DataFrame()

    # 3. Merge
    df_combined = pd.concat([df_prov, df_reg], ignore_index=True)

    # 4. Clean & Standardize
    df_combined['level'] = df_combined['level'].str.title().str.strip()
    df_combined['sex'] = df_combined['sex'].str.title().str.strip()

    corrections = {
        "Istanbul": "İstanbul", "Izmir": "İzmir", "Afyon": "Afyonkarahisar",
        "Agri": "Ağrı", "Canakkale": "Çanakkale", "Cankiri": "Çankırı",
        "Corum": "Çorum", "Diyarbakir": "Diyarbakır", "Eskisehir": "Eskişehir",
        "Gumushane": "Gümüşhane", "Hakkari": "Hakkâri", "Kahramanmaras": "Kahramanmaraş",
        "Kirklareli": "Kırklareli", "Kirsehir": "Kırşehir", "Kutahya": "Kütahya",
        "Mugla": "Muğla", "Mus": "Muş", "Nevsehir": "Nevşehir", "Nigde": "Niğde",
        "Sanliurfa": "Şanlıurfa", "Tekirdag": "Tekirdağ", "Usak": "Uşak",
        "Balikesir": "Balıkesir", "Bingol": "Bingöl", "Adiyaman": "Adıyaman",
        "Elazig": "Elazığ", "Aegean": "Aegean Region"
    }
    df_combined['level'] = df_combined['level'].replace(corrections)

    rate_map = {
        "q28": "Neonatal Mortality (q28d)", "q(28d)": "Neonatal Mortality (q28d)",
        "IMR": "Infant Mortality (q12m)", "q(12m)": "Infant Mortality (q12m)",
        "U5MR": "Under-5 Mortality (q5y)", "q(5y)": "Under-5 Mortality (q5y)"
    }
    df_combined['rate_label'] = df_combined['rate'].map(rate_map).fillna(df_combined['rate'])

    # Fallback fixes
    df_combined.loc[df_combined['rate'] == 'IMR', 'rate_label'] = "Infant Mortality (q12m)"
    df_combined.loc[df_combined['rate'] == 'U5MR', 'rate_label'] = "Under-5 Mortality (q5y)"

    return df_combined


@st.cache_data
def load_map_data():
    """Loads k-parameter data for historical maps."""
    path_ks = os.path.join("data", "part3_ks.xlsx")
    try:
        df = pd.read_excel(path_ks)
    except:
        # Try CSV if Excel fails
        try:
            df = pd.read_csv(path_ks.replace(".xlsx", ".csv"))
        except Exception as e:
            st.error(f"Error loading map data (part3_ks): {e}")
            return pd.DataFrame()

    df['level'] = df['level'].str.strip()
    df['sex'] = df['sex'].str.title().str.strip()
    return df


@st.cache_data
def load_geojson():
    path_geo = os.path.join("data", "tr-cities-utf8.json")
    try:
        with open(path_geo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None


# NUTS1 Mapping for Map Tab
NUTS1_MAPPING = {
    "Istanbul": ["İstanbul"],
    "West Marmara": ["Tekirdağ", "Edirne", "Kırklareli", "Balıkesir", "Çanakkale"],
    "Aegean": ["İzmir", "Aydın", "Denizli", "Muğla", "Manisa", "Afyonkarahisar", "Afyon", "Kütahya", "Uşak"],
    "East Marmara": ["Bursa", "Eskişehir", "Bilecik", "Kocaeli", "Sakarya", "Düzce", "Bolu", "Yalova"],
    "West Anatolia": ["Ankara", "Konya", "Karaman"],
    "Mediterranean": ["Antalya", "Isparta", "Burdur", "Adana", "Mersin", "Hatay", "Kahramanmaraş", "Osmaniye"],
    "Central Anatolia": ["Kırıkkale", "Aksaray", "Niğde", "Nevşehir", "Kırşehir", "Kayseri", "Sivas", "Yozgat"],
    "West Black Sea": ["Zonguldak", "Karabük", "Bartın", "Kastamonu", "Çankırı", "Sinop", "Samsun", "Tokat", "Çorum",
                       "Amasya"],
    "East Black Sea": ["Trabzon", "Ordu", "Giresun", "Rize", "Artvin", "Gümüşhane"],
    "Northeast Anatolia": ["Erzurum", "Erzincan", "Bayburt", "Ağrı", "Kars", "Iğdır", "Ardahan"],
    "Central East Anatolia": ["Malatya", "Elazığ", "Bingöl", "Tunceli", "Van", "Muş", "Bitlis", "Hakkâri"],
    "Southeast Anatolia": ["Gaziantep", "Adıyaman", "Kilis", "Şanlıurfa", "Diyarbakır", "Mardin", "Batman", "Şırnak",
                           "Siirt"]
}


@st.cache_data
def process_map_expansion(df):
    """Expands NUTS1 region data to provinces for plotting."""
    all_years = sorted(df['year'].unique())
    all_sexes = df['sex'].unique()
    all_regions = list(NUTS1_MAPPING.keys())

    full_index = pd.MultiIndex.from_product([all_years, all_sexes, all_regions], names=['year', 'sex', 'level'])
    df_filled = df.set_index(['year', 'sex', 'level']).reindex(full_index).reset_index()

    expanded_rows = []
    for _, row in df_filled.iterrows():
        region_name = row['level']
        if region_name in NUTS1_MAPPING:
            provinces = NUTS1_MAPPING[region_name]
            for province in provinces:
                new_row = row.to_dict()
                new_row['province_name'] = province
                new_row['region_name'] = region_name
                expanded_rows.append(new_row)
    return pd.DataFrame(expanded_rows)


# -----------------------------------------------------------------------------
# 3. LOAD ALL DATA
# -----------------------------------------------------------------------------
df_trends = load_trend_data()
df_map_raw = load_map_data()
turkey_geojson = load_geojson()

# -----------------------------------------------------------------------------
# 4. TABS INTERFACE
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["📈 Historical Trends", "🗺️ Regional Maps"])

# =============================================================================
# TAB 1: TRENDS (1. Kodunuz)
# =============================================================================
with tab1:
    st.header("📈 Historical Mortality Trends (Provinces & Regions)")

    if not df_trends.empty:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("### Filter Options")
            location_list = sorted(df_trends['level'].unique())
            default_ix = location_list.index("Ankara") if "Ankara" in location_list else 0
            selected_location = st.selectbox("Select Province or Region", location_list, index=default_ix)

            sex_options = df_trends['sex'].unique()
            selected_sex = st.radio("Select Sex", sex_options, index=0)

            st.info(
                "**Sources:**\n"
                "- **Provinces (1931-2008):** Vital records.\n"
                "- **Regions (1972-2008):** NUTS1 estimates."
            )

        with col2:
            # Filter
            filtered_df = df_trends[
                (df_trends['level'] == selected_location) &
                (df_trends['sex'] == selected_sex)
                ].sort_values("year")

            # Clean Neonatal < 1958
            filtered_df = filtered_df[
                ~((filtered_df['rate_label'].str.contains("Neonatal")) & (filtered_df['year'] < 1958))]

            if not filtered_df.empty:
                fig = px.line(
                    filtered_df, x="year", y="qx", color="rate_label", markers=True,
                    labels={"qx": "Probability of Dying", "year": "Year", "rate_label": "Indicator"},
                    title=f"Mortality Rates in {selected_location} ({selected_sex})",
                    color_discrete_map={
                        "Neonatal Mortality (q28d)": "#2ca02c",
                        "Infant Mortality (q12m)": "#1f77b4",
                        "Under-5 Mortality (q5y)": "#d62728"
                    }
                )
                fig.update_layout(height=500, xaxis=dict(dtick=5), hovermode="x unified",
                                  legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("View Data"):
                    st.dataframe(filtered_df[['year', 'sex', 'rate_label', 'qx']], use_container_width=True)
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, f"{selected_location}_trends.csv", "text/csv")
            else:
                st.warning("No data available.")
    else:
        st.error("Trend data could not be loaded.")

# =============================================================================
# TAB 2: MAPS (2. Kodunuz)
# =============================================================================
with tab2:
    st.header("🗺️ Regional (NUTS1) Mortality Patterns")

    if not df_map_raw.empty and turkey_geojson:
        # Precompute centroids
        region_centroids = {}
        prov_centroids = {}
        for feature in turkey_geojson['features']:
            name = feature['properties']['name']
            coords = feature['geometry']['coordinates']
            coords = coords[0][0] if feature['geometry']['type'] == 'MultiPolygon' else coords[0]
            prov_centroids[name] = (np.mean([p[1] for p in coords]), np.mean([p[0] for p in coords]))

        for region, provinces in NUTS1_MAPPING.items():
            lats, lons = [], []
            for prov in provinces:
                if prov in prov_centroids:
                    lats.append(prov_centroids[prov][0])
                    lons.append(prov_centroids[prov][1])
            if lats: region_centroids[region] = (np.mean(lats), np.mean(lons))

        # Prepare Data
        map_df = process_map_expansion(df_map_raw)

        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("### Map Settings")
            selected_sex_map = st.radio("Sex", ["Total", "Female", "Male"], key="map_sex")
            show_labels = st.checkbox("Show Region Labels", value=True)

            min_y = int(df_map_raw['year'].min())
            max_y = int(df_map_raw['year'].max())
            selected_year_map = st.slider("Year", min_y, max_y, 1990, key="map_year")

        with col2:
            filtered_map = map_df[
                (map_df['year'] == selected_year_map) &
                (map_df['sex'] == selected_sex_map)
                ]

            if not filtered_map.empty:
                fig_map = px.choropleth(
                    filtered_map,
                    geojson=turkey_geojson,
                    locations='province_name',
                    featureidkey="properties.name",
                    color='k',
                    color_continuous_scale="Reds",
                    range_color=(-1.5, 1.5),
                    hover_name='region_name',
                    hover_data={'province_name': False, 'k': ':.2f'},
                    title=f"NUTS1 Mortality Pattern in {selected_year_map} ({selected_sex_map})"
                )
                fig_map.update_traces(marker_line_width=0, marker_opacity=1.0)

                if show_labels:
                    unique_reg = filtered_map[['region_name', 'k']].drop_duplicates()
                    labels = []
                    for _, row in unique_reg.iterrows():
                        r_name = row['region_name']
                        k_val = row['k']
                        lbl_text = f"<b>{r_name}</b><br>{k_val:.2f}" if not pd.isna(k_val) else f"<b>{r_name}</b>"
                        if r_name in region_centroids:
                            lat, lon = region_centroids[r_name]
                            labels.append(dict(lat=lat, lon=lon, text=lbl_text))

                    lbl_df = pd.DataFrame(labels)
                    if not lbl_df.empty:
                        fig_map.add_trace(go.Scattergeo(
                            lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'],
                            mode='text', textfont=dict(size=10, color="black")
                        ))

                fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("No map data for selection.")
    else:
        st.error("Map data or GeoJSON missing.")