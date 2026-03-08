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
# 2. HELPER FUNCTIONS & DICTIONARIES
# -----------------------------------------------------------------------------
PROVINCE_CORRECTIONS = {
    "Istanbul": "İstanbul", "Izmir": "İzmir", "Afyon": "Afyonkarahisar", "Agri": "Ağrı", 
    "Canakkale": "Çanakkale", "Cankiri": "Çankırı", "Corum": "Çorum", "Diyarbakir": "Diyarbakır", 
    "Eskisehir": "Eskişehir", "Gumushane": "Gümüşhane", "Hakkari": "Hakkâri", "Kahramanmaras": "Kahramanmaraş",
    "Kirklareli": "Kırklareli", "Kirsehir": "Kırşehir", "Kutahya": "Kütahya", "Mugla": "Muğla", 
    "Mus": "Muş", "Nevsehir": "Nevşehir", "Nigde": "Niğde", "Sanliurfa": "Şanlıurfa", 
    "Tekirdag": "Tekirdağ", "Usak": "Uşak", "Balikesir": "Balıkesir", "Bingol": "Bingöl", 
    "Adiyaman": "Adıyaman", "Elazig": "Elazığ", "Gaziantep": "Gaziantep", "Duzce": "Düzce",
    "Igdir": "Iğdır", "Sirnak": "Şırnak", "Bartin": "Bartın", "Karabuk": "Karabük",
    "Zonguldak": "Zonguldak", "Mersin": "Mersin", "Icel": "Mersin"
}

NUTS1_MAPPING = {
    "Istanbul": ["İstanbul"],
    "West Marmara": ["Tekirdağ", "Edirne", "Kırklareli", "Balıkesir", "Çanakkale"],
    "Aegean": ["İzmir", "Aydın", "Denizli", "Muğla", "Manisa", "Afyonkarahisar", "Afyon", "Kütahya", "Uşak"],
    "East Marmara": ["Bursa", "Eskişehir", "Bilecik", "Kocaeli", "Sakarya", "Düzce", "Bolu", "Yalova"],
    "West Anatolia": ["Ankara", "Konya", "Karaman"],
    "Mediterranean": ["Antalya", "Isparta", "Burdur", "Adana", "Mersin", "Hatay", "Kahramanmaraş", "Osmaniye"],
    "Central Anatolia": ["Kırıkkale", "Aksaray", "Niğde", "Nevşehir", "Kırşehir", "Kayseri", "Sivas", "Yozgat"],
    "West Black Sea": ["Zonguldak", "Karabük", "Bartın", "Kastamonu", "Çankırı", "Sinop", "Samsun", "Tokat", "Çorum", "Amasya"],
    "East Black Sea": ["Trabzon", "Ordu", "Giresun", "Rize", "Artvin", "Gümüşhane"],
    "Northeast Anatolia": ["Erzurum", "Erzincan", "Bayburt", "Ağrı", "Kars", "Iğdır", "Ardahan"],
    "Central East Anatolia": ["Malatya", "Elazığ", "Bingöl", "Tunceli", "Van", "Muş", "Bitlis", "Hakkâri"],
    "Southeast Anatolia": ["Gaziantep", "Adıyaman", "Kilis", "Şanlıurfa", "Diyarbakır", "Mardin", "Batman", "Şırnak", "Siirt"]
}

PARENT_MAPPING_67 = {
    "Aksaray": "Niğde", "Bayburt": "Gümüşhane", "Karaman": "Konya",
    "Kırıkkale": "Ankara", "Batman": "Siirt", "Şırnak": "Siirt",
    "Bartın": "Zonguldak", "Karabük": "Zonguldak", "Iğdır": "Kars",
    "Ardahan": "Kars", "Yalova": "İstanbul", "Kilis": "Gaziantep",
    "Osmaniye": "Adana", "Düzce": "Bolu"
}

def process_regional_expansion(df):
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

def prepare_provincial_67_data(geojson_data):
    geo_provinces = []
    for feature in geojson_data['features']:
        geo_provinces.append(feature['properties']['name'])
    map_template = pd.DataFrame({'geo_province': geo_provinces})
    map_template['data_province'] = map_template['geo_province'].apply(lambda x: PARENT_MAPPING_67.get(x, x))
    return map_template, geo_provinces

def show_data_expander(df, filename="data.csv"):
    with st.expander("📊 View & Download Data"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=filename,
            mime='text/csv',
        )

def get_total_index(sex_options):
    sex_list = list(sex_options)
    return sex_list.index("Total") if "Total" in sex_list else 0

# -----------------------------------------------------------------------------
# 3. SHARED DATA LOADING FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_nat_qx_data():
    path = os.path.join("data", "part3_national_qx.xlsx")
    try:
        df = pd.read_excel(path)
    except:
        try:
            df = pd.read_csv(os.path.join("data", "part3_national_qx.xlsx - regional_sonuc.csv"))
        except Exception as e:
            st.error(f"Error loading national qx data: {e}")
            return pd.DataFrame()

    df['level'] = df['level'].str.title().str.strip()
    df['sex'] = df['sex'].str.title().str.strip()

    rate_col = 'upper_age' if 'upper_age' in df.columns else 'rate'
    df[rate_col] = df[rate_col].astype(str).str.replace(".0", "", regex=False)
    
    rate_map = {
        "28": "Neonatal Mortality (q28d)", "q28": "Neonatal Mortality (q28d)", "q(28d)": "Neonatal Mortality (q28d)",
        "IMR": "Infant Mortality (q12m)", "q(12m)": "Infant Mortality (q12m)",
        "U5MR": "Under-5 Mortality (q5y)", "q(5y)": "Under-5 Mortality (q5y)"
    }
    df['rate_label'] = df[rate_col].map(rate_map).fillna(df[rate_col])
    return df

@st.cache_data
def load_nat_k_data():
    path = os.path.join("data", "part3_ks_national.xlsx")
    try:
        df = pd.read_excel(path)
    except:
        try:
            df = pd.read_csv(os.path.join("data", "part3_ks_national.xlsx - ks.csv"))
        except Exception as e:
            st.error(f"Error loading national k data: {e}")
            return pd.DataFrame()
            
    df['level'] = df['level'].str.strip()
    df['sex'] = df['sex'].str.title().str.strip()
    return df

@st.cache_data
def load_prov_data():
    path_prov = os.path.join("data", "part3_prov_qx.xlsx")
    try:
        df = pd.read_excel(path_prov)
        df['level'] = df['level'].str.title().str.strip()
        df['level'] = df['level'].replace(PROVINCE_CORRECTIONS)
        df['sex'] = df['sex'].str.title().str.strip()

        rate_map = {
            "q28": "Neonatal Mortality (q28d)", "q(28d)": "Neonatal Mortality (q28d)",
            "IMR": "Infant Mortality (q12m)", "q(12m)": "Infant Mortality (q12m)",
            "U5MR": "Under-5 Mortality (q5y)", "q(5y)": "Under-5 Mortality (q5y)"
        }
        df['rate_label'] = df['rate'].map(rate_map).fillna(df['rate'])
        return df
    except Exception as e:
        st.error(f"Error loading province trend data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_reg_data():
    path_reg = os.path.join("data", "part3_region_qx.xlsx")
    try:
        df = pd.read_excel(path_reg)
        df = df.rename(columns={'upper_age': 'rate', 'p_qx': 'qx'})
        df['level'] = df['level'].str.title().str.strip()
        df['sex'] = df['sex'].str.title().str.strip()
        df['level'] = df['level'].replace({"Aegean": "Aegean Region"})

        rate_map = {
            "q28": "Neonatal Mortality (q28d)", "28": "Neonatal Mortality (q28d)",
            "IMR": "Infant Mortality (q12m)",
            "U5MR": "Under-5 Mortality (q5y)"
        }
        df['rate'] = df['rate'].astype(str).str.replace(".0", "", regex=False)
        df['rate_label'] = df['rate'].map(rate_map).fillna(df['rate'])
        return df
    except Exception as e:
        st.error(f"Error loading region trend data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_prov_map_k():
    path_ks = os.path.join("data", "part3_pro_ks.xlsx")
    try:
        df = pd.read_excel(path_ks)
    except:
        try:
            df = pd.read_csv(os.path.join("data", "part3_pro_ks.xlsx - Sayfa1.csv"))
            if df.shape[1] >= 5:
                df.columns = ['year', 'sex', 'province', 'type', 'k']
        except Exception as e:
            st.error(f"Error loading provincial k data: {e}")
            return pd.DataFrame()

    if 'province' not in df.columns:
        cols = df.columns
        df = df.rename(columns={cols[2]: 'province', cols[4]: 'k'})

    df['province'] = df['province'].str.strip()
    df['province'] = df['province'].replace(PROVINCE_CORRECTIONS)
    df['sex'] = df['sex'].str.title().str.strip()
    return df

@st.cache_data
def load_reg_map_k():
    path_ks = os.path.join("data", "part3_ks.xlsx")
    try:
        df = pd.read_excel(path_ks)
    except:
        try:
            df = pd.read_csv(path_ks.replace(".xlsx", ".csv"))
        except Exception as e:
            st.error(f"Error loading regional k data: {e}")
            return pd.DataFrame()

    df['level'] = df['level'].str.title().str.strip()
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

# -----------------------------------------------------------------------------
# 4. LOAD ALL DATA
# -----------------------------------------------------------------------------
df_nat_qx = load_nat_qx_data()
df_nat_k = load_nat_k_data()
df_prov_trends = load_prov_data()
df_reg_trends = load_reg_data()
df_prov_k = load_prov_map_k()
df_reg_k = load_reg_map_k()
turkey_geojson = load_geojson()


# -----------------------------------------------------------------------------
# 5. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("📌 Navigation")
st.sidebar.markdown("Select the geographic level of analysis:")

page = st.sidebar.radio("", [
    "🇹🇷 National Level",
    "🗺 Regional Level (NUTS-1)",
    "🏙️ Provincial Level"
])

st.sidebar.markdown("---")
st.sidebar.info("Use the tabs on the main screen to switch between trends and maps.")


# =============================================================================
# PAGE 1: NATIONAL LEVEL
# =============================================================================
if page == "🇹🇷 National Level":
    tab1, tab2 = st.tabs(["📉 Trends (qx)", "🧩 Patterns (k)"])

    with tab1:
        st.header("🇹🇷 Historical National Mortality Trends (qx)")
        if not df_nat_qx.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Settings")
                sex_opts = df_nat_qx['sex'].unique()
                selected_sex_nat_qx = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="t1_nat_qx_sex")

            with col2:
                filtered_nat_qx = df_nat_qx[df_nat_qx['sex'] == selected_sex_nat_qx].sort_values("year")
                if not filtered_nat_qx.empty:
                    fig_nat_qx = px.line(
                        filtered_nat_qx, x="year", y="qx", color="rate_label", markers=True,
                        title=f"National Mortality Trends ({selected_sex_nat_qx})",
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig_nat_qx.update_layout(height=500, xaxis=dict(dtick=5))
                    st.plotly_chart(fig_nat_qx, use_container_width=True)
                    
                    show_data_expander(filtered_nat_qx, f"historical_national_qx_{selected_sex_nat_qx}.csv")
                else:
                    st.warning("No data available.")

    with tab2:
        st.header("🇹🇷 Historical National Pattern (k parameter)")
        if not df_nat_k.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Chart Settings")
                available_sexes = df_nat_k['sex'].unique()
                view_mode = st.radio("View Mode", ["Single Sex", "Compare All Sexes"], index=1, key="t2_nat_k_mode")
                
                if view_mode == "Single Sex":
                    sel_sex_nat_k = st.selectbox("Select Sex", available_sexes, index=get_total_index(available_sexes), key="t2_nat_k_sex")
                    df_plot_k = df_nat_k[df_nat_k['sex'] == sel_sex_nat_k].sort_values("year")
                else:
                    df_plot_k = df_nat_k.sort_values("year")
                    
            with col2:
                if not df_plot_k.empty:
                    fig_nat_k = px.line(
                        df_plot_k, x="year", y="k", color="sex" if view_mode == "Compare All Sexes" else None,
                        markers=True, title="National Trend of Shape Parameter (k) over Time",
                        labels={"k": "Shape Parameter (k)", "year": "Year", "sex": "Sex"}
                    )
                    fig_nat_k.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Standard Pattern (k=0)")
                    fig_nat_k.update_layout(height=500, xaxis=dict(dtick=5))
                    st.plotly_chart(fig_nat_k, use_container_width=True)
                    
                    file_name_k = f"historical_national_k_{sel_sex_nat_k}.csv" if view_mode == "Single Sex" else "historical_national_k_all.csv"
                    show_data_expander(df_plot_k, file_name_k)
                else:
                    st.warning("No data to plot.")

# =============================================================================
# PAGE 2: 
# =============================================================================
elif page == "🗺 Regional Level (NUTS-1)":
    tab1, tab2 = st.tabs(["📉 Trends (qx)", "🗺️ Maps (k)"])

    with tab1:
        st.header("🗺 Historical Regional Mortality Trends (NUTS1)")
        if not df_reg_trends.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Settings")
                reg_list = sorted(df_reg_trends['level'].unique())
                selected_reg = st.selectbox("Select Region", reg_list, key="t3_sb")
                sex_opts = df_reg_trends['sex'].unique()
                selected_sex_reg = st.radio("Sex", sex_opts, index=get_total_index(sex_opts), key="t3_sex")
            with col2:
                filtered_reg = df_reg_trends[
                    (df_reg_trends['level'] == selected_reg) &
                    (df_reg_trends['sex'] == selected_sex_reg)
                ].sort_values("year")
                if not filtered_reg.empty:
                    fig_reg = px.line(
                        filtered_reg, x="year", y="qx", color="rate_label", markers=True,
                        title=f"{selected_reg} ({selected_sex_reg})",
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig_reg.update_layout(height=500, xaxis=dict(dtick=5))
                    st.plotly_chart(fig_reg, use_container_width=True)
                    
                    safe_reg_name = selected_reg.replace(" ", "_").lower()
                    show_data_expander(filtered_reg, f"historical_regional_qx_{safe_reg_name}_{selected_sex_reg}.csv")

    with tab2:
        st.header("🗺️ Regional (NUTS1) Maps")
        if not df_reg_k.empty and turkey_geojson:
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

            map_df = process_regional_expansion(df_reg_k)

            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown("### Map Settings")
                sex_opts = df_reg_k['sex'].unique()
                selected_sex_map = st.radio("Sex", sex_opts, index=get_total_index(sex_opts), key="t4_sex")
                min_yr, max_yr = int(df_reg_k['year'].min()), int(df_reg_k['year'].max())
                selected_year_map = st.slider("Year", min_yr, max_yr, max_yr, key="t4_year")
                show_reg_labels = st.checkbox("Show Region Names", value=True)

            with col2:
                filtered_map = map_df[(map_df['year'] == selected_year_map) & (map_df['sex'] == selected_sex_map)]

                if not filtered_map.empty:
                    sc1, sc2, sc3 = st.columns(3)
                    
                    nat_val_str = "N/A"
                    if not df_nat_k.empty:
                        nat_df = df_nat_k[(df_nat_k['year'] == selected_year_map) & (df_nat_k['sex'] == selected_sex_map)]
                        if not nat_df.empty: nat_val_str = f"{nat_df['k'].values[0]:.3f}"
                    sc1.metric("🇹🇷 National Average (k)", nat_val_str)

                    unique_reg = filtered_map[['region_name', 'k']].drop_duplicates().dropna(subset=['k'])
                    if not unique_reg.empty:
                        max_idx = unique_reg['k'].idxmax()
                        sc2.metric(f"📈 Highest: {unique_reg.loc[max_idx, 'region_name']}", f"{unique_reg.loc[max_idx, 'k']:.3f}")
                        min_idx = unique_reg['k'].idxmin()
                        sc3.metric(f"📉 Lowest: {unique_reg.loc[min_idx, 'region_name']}", f"{unique_reg.loc[min_idx, 'k']:.3f}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    fig_map = px.choropleth(
                        filtered_map, geojson=turkey_geojson, locations='province_name', featureidkey="properties.name",
                        color='k', color_continuous_scale="RdBu_r", range_color=(-1.5, 1.5), hover_name='region_name',
                        hover_data={'province_name': False, 'k': ':.2f'}, title=f"NUTS1 Mortality Pattern in {selected_year_map} ({selected_sex_map})"
                    )

                    fig_map.update_traces(marker_line_width=0, marker_opacity=1.0)

                    if show_reg_labels:
                        labels = []
                        for _, row in unique_reg.iterrows():
                            r_name, k_val = row['region_name'], row['k']
                            lbl_text = f"<b>{r_name}</b><br>{k_val:.2f}" if not pd.isna(k_val) else f"<b>{r_name}</b>"
                            if r_name in region_centroids:
                                labels.append(dict(lat=region_centroids[r_name][0], lon=region_centroids[r_name][1], text=lbl_text))

                        lbl_df = pd.DataFrame(labels)
                        if not lbl_df.empty:
                            fig_map.add_trace(go.Scattergeo(lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'], mode='text', textfont=dict(size=10, color="black")))

                    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                    fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                    st.plotly_chart(fig_map, use_container_width=True)
                    
                    c1, c2, c3 = st.columns([1, 1, 2])
                    with c1: st.info("🟥 **Red areas:** Late Pattern (High k)")
                    with c2: st.info("🟦 **Blue areas:** Early Pattern (Low k)")
                    st.markdown("""<div style="background-color: #dcedc8; padding: 10px; border-radius: 5px; color: #333; font-size: 14px; margin-top: -10px; border: 1px solid #c5e1a5;">ℹ️ <b>Note:</b> Green areas indicate missing data.</div>""", unsafe_allow_html=True)
                    
                    show_data_expander(filtered_map, f"historical_regional_map_{selected_year_map}_{selected_sex_map}.csv")
                else:
                    st.warning("No data available.")

# =============================================================================
# PAGE 3: PROVINCIAL LEVEL
# =============================================================================
elif page == "🏙️ Provincial Level":
    tab1, tab2 = st.tabs(["📉 Trends (qx)", "🗺️ Maps (67 Provinces)"])

    with tab1:
        st.header("🏙️ Historical Provincial Mortality Trends (1931-2008)")
        if not df_prov_trends.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("### Settings")
                prov_list = sorted(df_prov_trends['level'].unique())
                default_ix = prov_list.index("İstanbul") if "İstanbul" in prov_list else 0
                selected_prov = st.selectbox("Select Province", prov_list, index=default_ix, key="t5_sb")
                sex_opts = df_prov_trends['sex'].unique()
                selected_sex = st.radio("Sex", sex_opts, index=get_total_index(sex_opts), key="t5_sex")
            with col2:
                filtered_df = df_prov_trends[
                    (df_prov_trends['level'] == selected_prov) &
                    (df_prov_trends['sex'] == selected_sex)
                ].sort_values("year")
                
                # 1958 öncesi Neonatal gizleniyor (orijinal kodda vardı)
                filtered_df = filtered_df[~((filtered_df['rate_label'].str.contains("Neonatal")) & (filtered_df['year'] < 1958))]
                    
                if not filtered_df.empty:
                    fig = px.line(
                        filtered_df, x="year", y="qx", color="rate_label", markers=True,
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator"},
                        title=f"{selected_prov} ({selected_sex})",
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig.update_layout(height=500, xaxis=dict(dtick=5), legend=dict(orientation="h", y=1.1))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    safe_prov_name = selected_prov.replace(" ", "_").lower()
                    show_data_expander(filtered_df, f"historical_provincial_qx_{safe_prov_name}_{selected_sex}.csv")
                else:
                    st.warning("No data.")

    with tab2:
        st.header("🗺️ Provincial Mortality Map (Historical 67 Provinces)")
        if not df_prov_k.empty and turkey_geojson:
            geo_centroids = {}
            valid_map_names = []
            for feature in turkey_geojson['features']:
                name = feature['properties']['name']
                valid_map_names.append(name)
                coords = feature['geometry']['coordinates']
                coords = coords[0][0] if feature['geometry']['type'] == 'MultiPolygon' else coords[0]
                geo_centroids[name] = (np.mean([p[1] for p in coords]), np.mean([p[0] for p in coords]))

            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown("### Settings")
                sex_opts = ["Total", "Female", "Male"]
                map_sex_prov = st.radio("Sex", sex_opts, index=0, key="t6_sex")
                min_y, max_y = int(df_prov_k['year'].min()), int(df_prov_k['year'].max())
                map_year_prov = st.slider("Year", min_y, max_y, max_y, key="t6_year")
                st.markdown("---")
                show_prov_names = st.checkbox("Show Province Names", value=False)
                show_k_values = st.checkbox("Show k Values", value=False)

            with col2:
                raw_k_data = df_prov_k[(df_prov_k['year'] == map_year_prov) & (df_prov_k['sex'] == map_sex_prov)]
                template_df, _ = prepare_provincial_67_data(turkey_geojson)
                
                sc1, sc2, sc3 = st.columns(3)
                nat_val_str = "N/A"
                if not df_nat_k.empty:
                    nat_df = df_nat_k[(df_nat_k['year'] == map_year_prov) & (df_nat_k['sex'] == map_sex_prov)]
                    if not nat_df.empty: nat_val_str = f"{nat_df['k'].values[0]:.3f}"
                sc1.metric("🇹🇷 National Average (k)", nat_val_str)
                
                raw_k_clean = raw_k_data.dropna(subset=['k'])
                if not raw_k_clean.empty:
                    max_idx = raw_k_clean['k'].idxmax()
                    sc2.metric(f"📈 Highest: {raw_k_clean.loc[max_idx, 'province']}", f"{raw_k_clean.loc[max_idx, 'k']:.3f}")
                    min_idx = raw_k_clean['k'].idxmin()
                    sc3.metric(f"📉 Lowest: {raw_k_clean.loc[min_idx, 'province']}", f"{raw_k_clean.loc[min_idx, 'k']:.3f}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if not raw_k_data.empty:
                    merged_map_data = template_df.merge(raw_k_data, left_on='data_province', right_on='province', how='left')
                else:
                    merged_map_data = template_df
                    merged_map_data['k'] = np.nan

                fig_map = px.choropleth(
                    merged_map_data, geojson=turkey_geojson, locations='geo_province', featureidkey="properties.name",
                    color='k', color_continuous_scale="RdBu_r", range_color=(-1.5, 1.5), hover_name='data_province',
                    hover_data={'geo_province': False, 'k': ':.2f'}, title=f"Provincial k-Parameter: {map_year_prov} ({map_sex_prov})"
                )

                fig_map.update_traces(marker_line_width=0, marker_opacity=1.0)

                bg_trace = go.Choropleth(
                    geojson=turkey_geojson, locations=valid_map_names, featureidkey="properties.name",
                    z=[1] * len(valid_map_names), colorscale=[[0, '#dcedc8'], [1, '#dcedc8']],
                    showscale=False, marker_line_width=0.1, marker_line_color="black", hoverinfo='skip'
                )
                fig_map.add_trace(bg_trace)
                fig_map.data = (fig_map.data[-1],) + fig_map.data[:-1]

                if show_prov_names or show_k_values:
                    labels = []
                    available_parents = raw_k_data['province'].dropna().unique()
                    for parent_name in available_parents:
                        k_val = raw_k_data[raw_k_data['province'] == parent_name]['k'].iloc[0]
                        if parent_name in geo_centroids:
                            lat, lon = geo_centroids[parent_name]
                            label_parts = []
                            if show_prov_names: label_parts.append(f"<b>{parent_name}</b>")
                            if show_k_values and not pd.isna(k_val): label_parts.append(f"{k_val:.2f}")
                            if label_parts: labels.append(dict(lat=lat, lon=lon, text="<br>".join(label_parts)))

                    lbl_df = pd.DataFrame(labels)
                    if not lbl_df.empty:
                        fig_map.add_trace(go.Scattergeo(lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'], mode='text', textfont=dict(size=9, color="black")))

                fig_map.update_geos(fitbounds="locations", visible=False, showland=True, landcolor="#f0f0f0", showcountries=True, countrycolor="white")
                fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig_map, use_container_width=True)

                c1, c2, c3 = st.columns([1, 1, 2])
                with c1: st.info("🟥 **Red areas:** Late Pattern (High k)")
                with c2: st.info("🟦 **Blue areas:** Early Pattern (Low k)")
                st.markdown("""<div style="background-color: #dcedc8; padding: 10px; border-radius: 5px; color: #333; font-size: 14px; margin-top: 10px; border: 1px solid #c5e1a5;">ℹ️ <b>Note:</b> Green areas indicate missing data.</div>""", unsafe_allow_html=True)

                show_data_expander(merged_map_data, f"historical_provincial_map_67_{map_year_prov}_{map_sex_prov}.csv")