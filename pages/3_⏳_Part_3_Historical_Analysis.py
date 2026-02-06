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

# --- A. PROVINCIAL TREND DATA ---
@st.cache_data
def load_prov_data():
    path_prov = os.path.join("data", "part3_prov_qx.xlsx")
    try:
        df = pd.read_excel(path_prov)
        df['level'] = df['level'].str.title().str.strip()
        df['sex'] = df['sex'].str.title().str.strip()

        corrections = {
            "Istanbul": "İstanbul", "Izmir": "İzmir", "Afyon": "Afyonkarahisar",
            "Agri": "Ağrı", "Canakkale": "Çanakkale", "Cankiri": "Çankırı",
            "Corum": "Çorum", "Diyarbakir": "Diyarbakır", "Eskisehir": "Eskişehir",
            "Gumushane": "Gümüşhane", "Hakkari": "Hakkâri", "Kahramanmaras": "Kahramanmaraş",
            "Kirklareli": "Kırklareli", "Kirsehir": "Kırşehir", "Kutahya": "Kütahya",
            "Mugla": "Muğla", "Mus": "Muş", "Nevsehir": "Nevşehir", "Nigde": "Niğde",
            "Sanliurfa": "Şanlıurfa", "Tekirdag": "Tekirdağ", "Usak": "Uşak",
            "Balikesir": "Balıkesir", "Bingol": "Bingöl", "Adiyaman": "Adıyaman",
            "Elazig": "Elazığ"
        }
        df['level'] = df['level'].replace(corrections)

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


# --- B. REGIONAL TREND DATA ---
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
            "q28": "Neonatal Mortality (q28d)",
            "IMR": "Infant Mortality (q12m)",
            "U5MR": "Under-5 Mortality (q5y)"
        }
        df['rate_label'] = df['rate'].map(rate_map).fillna(df['rate'])
        df.loc[df['rate'] == 'IMR', 'rate_label'] = "Infant Mortality (q12m)"
        df.loc[df['rate'] == 'U5MR', 'rate_label'] = "Under-5 Mortality (q5y)"
        return df
    except Exception as e:
        st.error(f"Error loading region trend data: {e}")
        return pd.DataFrame()


# --- C. PROVINCIAL MAP DATA (k values) ---
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
    df['sex'] = df['sex'].str.title().str.strip()

    replacements = {
        "Afyon": "Afyonkarahisar",
        "Icel": "Mersin", "İçel": "Mersin",
        "K. Maras": "Kahramanmaraş", "K.Maraş": "Kahramanmaraş"
    }
    df['province'] = df['province'].replace(replacements)
    return df


# --- D. REGIONAL MAP DATA (k values) ---
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

    df['level'] = df['level'].str.strip()
    df['sex'] = df['sex'].str.title().str.strip()
    return df


# --- E. GEOJSON ---
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
# 3. MAPPING LOGICS & UTILS
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# 4. LOAD ALL DATA
# -----------------------------------------------------------------------------
df_prov_trends = load_prov_data()
df_reg_trends = load_reg_data()
df_prov_k = load_prov_map_k()
df_reg_k = load_reg_map_k()
turkey_geojson = load_geojson()

# -----------------------------------------------------------------------------
# 5. TABS INTERFACE
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏙️ Provincial Trends",
    "🗺️ Provincial Maps (67)",
    "🌍 Regional Trends",
    "🗺️ Regional Maps"
])

# =============================================================================
# TAB 1: PROVINCIAL TRENDS
# =============================================================================
with tab1:
    st.header("🏙️ Provincial Mortality Trends (1931-2008)")
    if not df_prov_trends.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            prov_list = sorted(df_prov_trends['level'].unique())
            default_ix = prov_list.index("İstanbul") if "İstanbul" in prov_list else 0
            selected_prov = st.selectbox("Select Province", prov_list, index=default_ix, key="t1_sb")
            selected_sex = st.radio("Sex", df_prov_trends['sex'].unique(), index=0, key="t1_sex")
        with col2:
            filtered_df = df_prov_trends[
                (df_prov_trends['level'] == selected_prov) &
                (df_prov_trends['sex'] == selected_sex)
                ].sort_values("year")
            filtered_df = filtered_df[
                ~((filtered_df['rate_label'].str.contains("Neonatal")) & (filtered_df['year'] < 1958))]
            if not filtered_df.empty:
                fig = px.line(
                    filtered_df, x="year", y="qx", color="rate_label", markers=True,
                    labels={"qx": "Probability of Dying", "rate_label": "Indicator"},
                    title=f"{selected_prov} ({selected_sex})",
                    color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4",
                                        "Under-5 Mortality (q5y)": "#d62728"}
                )
                fig.update_layout(height=500, xaxis=dict(dtick=5), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data.")

# =============================================================================
# TAB 2: PROVINCIAL MAPS (67 Province Logic - Merged Appearance)
# =============================================================================
with tab2:
    st.header("🗺️ Provincial Mortality Map (Historical 67 Provinces)")

    if not df_prov_k.empty and turkey_geojson:
        # Hazırlık
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
            map_sex_prov = st.radio("Sex", ["Total", "Female", "Male"], key="t2_sex")
            min_y, max_y = int(df_prov_k['year'].min()), int(df_prov_k['year'].max())
            map_year_prov = st.slider("Year", min_y, max_y, 1972, key="t2_year")

            st.markdown("---")
            show_prov_names = st.checkbox("Show Province Names", value=False)
            show_k_values = st.checkbox("Show k Values", value=False)

        with col2:
            raw_k_data = df_prov_k[
                (df_prov_k['year'] == map_year_prov) &
                (df_prov_k['sex'] == map_sex_prov)
                ]
            template_df, _ = prepare_provincial_67_data(turkey_geojson)
            if not raw_k_data.empty:
                merged_map_data = template_df.merge(
                    raw_k_data,
                    left_on='data_province',
                    right_on='province',
                    how='left'
                )
            else:
                merged_map_data = template_df
                merged_map_data['k'] = np.nan

            fig_map = px.choropleth(
                merged_map_data,
                geojson=turkey_geojson,
                locations='geo_province',
                featureidkey="properties.name",
                color='k',
                color_continuous_scale="RdBu_r",
                range_color=(-1.5, 1.5),
                hover_name='data_province',  # Hover'da Kırıkkale üstüne gelseniz de ANKARA yazar
                hover_data={'geo_province': False, 'k': ':.2f'},
                title=f"Provincial k-Parameter: {map_year_prov} ({map_sex_prov})"
            )

            # *** ÖNEMLİ DÜZELTME: Sınırları Kaldır (Görsel Birleştirme) ***
            # marker_line_width=0 yaparak aynı renkteki illerin (Ankara-Kırıkkale)
            # birleşik gibi görünmesini sağlıyoruz.
            fig_map.update_traces(marker_line_width=0, marker_opacity=1.0)
            # -------------------------------------------------------------

            # Arka plan (Missing Data) - Buna ince bir çizgi ekleyebiliriz veya kaldırabiliriz
            bg_trace = go.Choropleth(
                geojson=turkey_geojson,
                locations=valid_map_names,
                featureidkey="properties.name",
                z=[1] * len(valid_map_names),
                colorscale=[[0, '#dcedc8'], [1, '#dcedc8']],
                showscale=False,
                marker_line_width=0.1,  # Arka planda iller silik de olsa belli olsun
                marker_line_color="black",
                hoverinfo='skip'
            )
            fig_map.add_trace(bg_trace)
            fig_map.data = (fig_map.data[-1],) + fig_map.data[:-1]

            # Etiketler: Sadece Verisi Olan "Parent" İllerin Merkezine
            if show_prov_names or show_k_values:
                labels = []
                # Burada raw_k_data (yani 67 il verisi) üzerinden dönüyoruz
                # Böylece etiketi sadece "Ankara" için koyarız, "Kırıkkale" için koymayız.
                available_parents = raw_k_data['province'].dropna().unique()

                # Etiket oluşturmak için merged data'dan ziyade Parent listesini kullanmak daha temiz
                # Ancak k değerine erişmek için raw_k_data lazım.
                for parent_name in available_parents:
                    # Parent ilin k değerini al
                    k_val = raw_k_data[raw_k_data['province'] == parent_name]['k'].iloc[0]

                    # Parent ilin koordinatını bul (GeoJSON'da bu isimde il varsa)
                    if parent_name in geo_centroids:
                        lat, lon = geo_centroids[parent_name]
                        label_parts = []
                        if show_prov_names: label_parts.append(f"<b>{parent_name}</b>")
                        if show_k_values and not pd.isna(k_val): label_parts.append(f"{k_val:.2f}")

                        if label_parts:
                            labels.append(dict(lat=lat, lon=lon, text="<br>".join(label_parts)))

                lbl_df = pd.DataFrame(labels)
                if not lbl_df.empty:
                    fig_map.add_trace(go.Scattergeo(
                        lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'],
                        mode='text', textfont=dict(size=9, color="black")
                    ))

            fig_map.update_geos(fitbounds="locations", visible=False, showland=True, landcolor="#f0f0f0",
                                showcountries=True, countrycolor="white")
            fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
            st.plotly_chart(fig_map, use_container_width=True)

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                st.info("🟥 **Red areas:** Late Pattern (High k)")
            with c2:
                st.info("🟦 **Blue areas:** Early Pattern (Low k)")
            st.markdown(
                """<div style="background-color: #dcedc8; padding: 10px; border-radius: 5px; color: #333; font-size: 14px; margin-top: 10px; border: 1px solid #c5e1a5;">ℹ️ <b>Note:</b> Green areas indicate missing data.</div>""",
                unsafe_allow_html=True)

# =============================================================================
# TAB 3: REGIONAL TRENDS
# =============================================================================
with tab3:
    st.header("🌍 Regional Mortality Trends (NUTS1)")
    if not df_reg_trends.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            reg_list = sorted(df_reg_trends['level'].unique())
            selected_reg = st.selectbox("Select Region", reg_list, key="t3_sb")
            selected_sex_reg = st.radio("Sex", df_reg_trends['sex'].unique(), index=0, key="t3_sex")
        with col2:
            filtered_reg = df_reg_trends[
                (df_reg_trends['level'] == selected_reg) &
                (df_reg_trends['sex'] == selected_sex_reg)
                ].sort_values("year")
            if not filtered_reg.empty:
                fig_reg = px.line(
                    filtered_reg, x="year", y="qx", color="rate_label", markers=True,
                    title=f"{selected_reg} ({selected_sex_reg})"
                )
                st.plotly_chart(fig_reg, use_container_width=True)

# =============================================================================
# TAB 4: REGIONAL MAPS (NUTS1 BLOCKS)
# =============================================================================
with tab4:
    st.header("🗺️ Regional (NUTS1) Maps")
    if not df_reg_k.empty and turkey_geojson:
        # 1. Bölge Merkezlerini Hesapla
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
            selected_sex_map = st.radio("Sex", ["Total", "Female", "Male"], key="t4_sex")
            selected_year_map = st.slider("Year", int(df_reg_k['year'].min()), int(df_reg_k['year'].max()), 1990,
                                          key="t4_year")
            show_reg_labels = st.checkbox("Show Region Names", value=True)

        with col2:
            filtered_map = map_df[
                (map_df['year'] == selected_year_map) &
                (map_df['sex'] == selected_sex_map)
                ]

            if not filtered_map.empty:
                # 2. Bölgesel Harita Çizimi
                fig_map = px.choropleth(
                    filtered_map,
                    geojson=turkey_geojson,
                    locations='province_name',
                    featureidkey="properties.name",
                    color='k',
                    color_continuous_scale="RdBu_r",
                    range_color=(-1.5, 1.5),
                    hover_name='region_name',
                    hover_data={'province_name': False, 'k': ':.2f'},
                    title=f"NUTS1 Mortality Pattern in {selected_year_map} ({selected_sex_map})"
                )

                # *** KRİTİK AYAR: Sınır Çizgilerini Kaldır ***
                fig_map.update_traces(marker_line_width=0, marker_opacity=1.0)
                # -----------------------------------------------

                # 3. Bölge İsimleri (Etiketler)
                if show_reg_labels:
                    unique_reg = filtered_map[['region_name', 'k']].drop_duplicates()
                    labels = []
                    for _, row in unique_reg.iterrows():
                        r_name = row['region_name']
                        k_val = row['k']
                        lbl_text = f"<b>{r_name}</b><br>{k_val:.2f}" if not pd.isna(k_val) else f"<b>{r_name}</b>"
                        if r_name in region_centroids:
                            labels.append(
                                dict(lat=region_centroids[r_name][0], lon=region_centroids[r_name][1], text=lbl_text))

                    lbl_df = pd.DataFrame(labels)
                    if not lbl_df.empty:
                        fig_map.add_trace(
                            go.Scattergeo(lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'], mode='text',
                                          textfont=dict(size=10, color="black")))

                fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig_map, use_container_width=True)
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.info("🟥 **Red areas:** Late Pattern (High k)")
                with c2:
                    st.info("🟦 **Blue areas:** Early Pattern (Low k)")
                st.markdown(
                    """
                    <div style="background-color: #dcedc8; padding: 10px; border-radius: 5px; color: #333; font-size: 14px; margin-top: -10px; border: 1px solid #c5e1a5;">
                    ℹ️ <b>Note:</b> Green areas indicate missing data for the selected year/sex (within Türkiye).
                    </div>
                    """, unsafe_allow_html=True
                )