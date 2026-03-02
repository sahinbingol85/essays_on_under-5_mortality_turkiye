import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Part 1: Recent Trends (2009-2024)",
    page_icon="📍",
    layout="wide"
)

st.title("📍 Part 1: Mortality Analysis (2009–2024)")
st.markdown("Detailed analysis of mortality trends and spatial patterns for Türkiye.")

# -----------------------------------------------------------------------------
# 2. YARDIMCI FONKSİYONLAR
# -----------------------------------------------------------------------------
NUTS1_MAPPING = {
    "Istanbul": ["İstanbul"],
    "West Marmara": ["Tekirdağ", "Edirne", "Kırklareli", "Balıkesir", "Çanakkale"],
    "Aegean": ["İzmir", "Aydın", "Denizli", "Muğla", "Manisa", "Afyonkarahisar", "Kütahya", "Uşak"],
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

def process_regional_expansion(df):
    all_years = sorted(df['year'].unique())
    all_sexes = df['sex'].unique()
    all_regions = list(NUTS1_MAPPING.keys())
    
    # Eksik yılları/cinsiyetleri doldur (tam MultiIndex)
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

# Veriyi Gösterme ve İndirme Butonu Fonksiyonu
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

# -----------------------------------------------------------------------------
# 3. VERİ YÜKLEME (DATA KLASÖRÜNDEN)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    def load_file(base_name):
        possible_names = [f"data/{base_name}.csv", f"data/{base_name}.xlsx", 
                          f"data/{base_name.replace('_', '-')}.csv", f"data/{base_name.replace('_', '-')}.xlsx"]
        for p in possible_names:
            if os.path.exists(p):
                return pd.read_csv(p) if p.endswith('.csv') else pd.read_excel(p)
        return pd.DataFrame()

    df_qx = load_file("part1_qx")
    df_k = load_file("part1_ks")
    df_reg_qx = load_file("part1_qx_regional")
    df_reg_k = load_file("part1_ks_regional")
    df_nat_qx = load_file("part1_qx_national")
    df_nat_k = load_file("part1_ks_national")

    # --- VERİ TEMİZLİĞİ VE STANDARTLAŞTIRMA ---
    corrections = {
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

    region_map = {
        'aegean': 'Aegean', 'east_blacksea': 'East Black Sea', 'east_marmara': 'East Marmara',
        'istanbul': 'Istanbul', 'mediterranean': 'Mediterranean', 'middle_anatolia': 'Central Anatolia',          
        'middle_east_anatolia': 'Central East Anatolia', 'north_east_anatolia': 'Northeast Anatolia',     
        'south_east_anatolia': 'Southeast Anatolia', 'west_anatolia': 'West Anatolia',
        'west_blacksea': 'West Black Sea', 'west_marmara': 'West Marmara'
    }

    rate_map = {"q28": "Neonatal Mortality (q28d)", "IMR": "Infant Mortality (q12m)", "U5MR": "Under-5 Mortality (q5y)"}
    for df in [df_qx, df_reg_qx, df_nat_qx]:
        if not df.empty:
            rate_col = 'upper_age' if 'upper_age' in df.columns else ('rate' if 'rate' in df.columns else None)
            if rate_col:
                df['rate_label'] = df[rate_col].map(rate_map).fillna(df[rate_col])
            if 'sex' in df.columns:
                df['sex'] = df['sex'].str.title().str.strip()

    for df in [df_reg_k, df_reg_qx]:
        if not df.empty and 'level' in df.columns:
            df['level'] = df['level'].str.strip().str.lower().replace(region_map)
        if not df.empty and 'sex' in df.columns:
            df['sex'] = df['sex'].str.title().str.strip()

    if not df_nat_k.empty and 'sex' in df_nat_k.columns:
        df_nat_k['sex'] = df_nat_k['sex'].str.title().str.strip()

    for df in [df_qx, df_k]:
        if not df.empty and 'level' in df.columns:
            df['level'] = df['level'].str.title().str.strip()
            df['level'] = df['level'].replace(corrections)
        if not df.empty and 'sex' in df.columns:
            df['sex'] = df['sex'].str.title().str.strip()

    return df_qx, df_k, df_reg_qx, df_reg_k, df_nat_qx, df_nat_k

@st.cache_data
def load_map_resources():
    file_name = "data/tr-cities-utf8.json"
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    except:
        st.error(f"Map file '{file_name}' not found.")
        st.stop()

    centroids = {}
    valid_provinces = []
    for feature in geojson['features']:
        name = feature['properties']['name']
        valid_provinces.append(name)
        coords = feature['geometry']['coordinates']
        coords = coords[0][0] if feature['geometry']['type'] == 'MultiPolygon' else coords[0]
        lon = np.mean([p[0] for p in coords])
        lat = np.mean([p[1] for p in coords])
        centroids[name] = (lat, lon)

    return geojson, centroids, valid_provinces

try:
    df_qx, df_k, df_reg_qx, df_reg_k, df_nat_qx, df_nat_k = load_data()
    turkey_geojson, province_centroids, valid_map_names = load_map_resources()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 4. ARAYÜZ (TABS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🇹🇷 National Trends (qx)", 
    "🇹🇷 National Patterns (k)", 
    "🗺️ Regional Trends (qx)", 
    "🗺️ Regional Maps (k)", 
    "📈 Provincial Trends (qx)", 
    "🗺️ Provincial Maps (k)"
])

# =============================================================================
# TAB 1: NATIONAL TRENDS (qx)
# =============================================================================
with tab1:
    st.header("🇹🇷 National Trends in Mortality Levels (qx)")
    if not df_nat_qx.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Settings")
            selected_sex_nat_qx = st.radio("Select Sex", df_nat_qx['sex'].unique(), index=0, key="nat_qx_sex")

        with col2:
            filtered_nat_qx = df_nat_qx[df_nat_qx['sex'] == selected_sex_nat_qx].sort_values("year")
            if not filtered_nat_qx.empty:
                fig_nat_qx = px.line(
                    filtered_nat_qx, x="year", y="qx", color="rate_label", markers=True,
                    title=f"National Mortality Trends ({selected_sex_nat_qx})",
                    labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                    color_discrete_map={
                        "Neonatal Mortality (q28d)": "#2ca02c",
                        "Infant Mortality (q12m)": "#1f77b4",
                        "Under-5 Mortality (q5y)": "#d62728"
                    }
                )
                fig_nat_qx.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_nat_qx, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                show_data_expander(filtered_nat_qx, f"national_qx_{selected_sex_nat_qx}.csv")
            else:
                st.warning("No data available.")
    else:
        st.error("National qx data not found. Please upload to the data folder.")

# =============================================================================
# TAB 2: NATIONAL PATTERNS (k)
# =============================================================================
with tab2:
    st.header("🇹🇷 National Trend of Mortality Pattern (k parameter)")
    if not df_nat_k.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Chart Settings")
            available_sexes = df_nat_k['sex'].unique()
            view_mode = st.radio("View Mode", ["Single Sex", "Compare All Sexes"], index=1, key="nat_k_mode")
            
            if view_mode == "Single Sex":
                sel_sex_nat_k = st.selectbox("Select Sex", available_sexes, key="nat_k_sex")
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
                fig_nat_k.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_nat_k, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                file_name_k = f"national_k_{sel_sex_nat_k}.csv" if view_mode == "Single Sex" else "national_k_all.csv"
                show_data_expander(df_plot_k, file_name_k)
            else:
                st.warning("No data to plot.")
    else:
        st.error("National ks data not found.")

# =============================================================================
# TAB 3: REGIONAL TRENDS (qx)
# =============================================================================
with tab3:
    st.header("🗺️ Regional Trends in Mortality Levels (qx)")
    if not df_reg_qx.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Settings")
            regions = sorted(df_reg_qx['level'].unique())
            selected_region = st.selectbox("Select Region (NUTS-1)", regions)
            selected_sex_reg_qx = st.radio("Select Sex", df_reg_qx['sex'].unique(), index=0, key="reg_qx_sex")

        with col2:
            filtered_reg_qx = df_reg_qx[(df_reg_qx['level'] == selected_region) & (df_reg_qx['sex'] == selected_sex_reg_qx)].sort_values("year")
            if not filtered_reg_qx.empty:
                fig_reg_qx = px.line(
                    filtered_reg_qx, x="year", y="qx", color="rate_label", markers=True,
                    title=f"Mortality Trends in {selected_region} ({selected_sex_reg_qx})",
                    labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                    color_discrete_map={
                        "Neonatal Mortality (q28d)": "#2ca02c",
                        "Infant Mortality (q12m)": "#1f77b4",
                        "Under-5 Mortality (q5y)": "#d62728"
                    }
                )
                fig_reg_qx.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_reg_qx, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                safe_reg_name = selected_region.replace(" ", "_").lower()
                show_data_expander(filtered_reg_qx, f"regional_qx_{safe_reg_name}_{selected_sex_reg_qx}.csv")
            else:
                st.warning("No data available.")
    else:
        st.error("Regional qx data not found.")

# =============================================================================
# TAB 4: REGIONAL MAPS (k)
# =============================================================================
with tab4:
    st.header("🗺️ Regional Mortality Maps (NUTS-1 k parameter)")
    if not df_reg_k.empty:
        region_centroids = {}
        for region, provinces in NUTS1_MAPPING.items():
            lats, lons = [], []
            for prov in provinces:
                if prov in province_centroids:
                    lats.append(province_centroids[prov][0])
                    lons.append(province_centroids[prov][1])
            if lats: region_centroids[region] = (np.mean(lats), np.mean(lons))

        map_df = process_regional_expansion(df_reg_k)

        r_col1, r_col2 = st.columns([1, 4])
        with r_col1:
            st.markdown("### Map Settings")
            r_years = sorted(df_reg_k['year'].unique())
            selected_year_reg = st.select_slider("Select Year", options=r_years, value=r_years[-1] if r_years else 2023, key="reg_map_y")
            selected_sex_reg = st.radio("Select Sex", df_reg_k['sex'].unique(), index=0, key="reg_map_sex")
            show_reg_labels = st.checkbox("Show Region Names", value=True)

        with r_col2:
            filtered_reg_map = map_df[(map_df['year'] == selected_year_reg) & (map_df['sex'] == selected_sex_reg)]
            if not filtered_reg_map.empty:
                fig_reg_map = px.choropleth(
                    filtered_reg_map, geojson=turkey_geojson, locations='province_name', featureidkey="properties.name",
                    color='k', color_continuous_scale="RdBu_r", range_color=(-2.0, 2.0), hover_name='region_name',
                    hover_data={'province_name': False, 'k': ':.2f'}, title=f"NUTS1 Mortality Pattern in {selected_year_reg} ({selected_sex_reg})"
                )
                fig_reg_map.update_traces(marker_line_width=0, marker_opacity=1.0)

                if show_reg_labels:
                    unique_reg = filtered_reg_map[['region_name', 'k']].drop_duplicates()
                    labels = []
                    for _, row in unique_reg.iterrows():
                        r_name = row['region_name']
                        k_val = row['k']
                        lbl_text = f"<b>{r_name}</b><br>{k_val:.2f}" if not pd.isna(k_val) else f"<b>{r_name}</b>"
                        if r_name in region_centroids:
                            labels.append(dict(lat=region_centroids[r_name][0], lon=region_centroids[r_name][1], text=lbl_text))

                    lbl_df = pd.DataFrame(labels)
                    if not lbl_df.empty:
                        fig_reg_map.add_trace(go.Scattergeo(lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'], mode='text', textfont=dict(size=10, color="black")))

                fig_reg_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                fig_reg_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig_reg_map, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                show_data_expander(filtered_reg_map, f"regional_map_k_{selected_year_reg}_{selected_sex_reg}.csv")
            else:
                st.warning("No regional data available for the selected year and sex.")
    else:
        st.error("Regional ks data not found.")

# =============================================================================
# TAB 5: PROVINCIAL TRENDS (qx)
# =============================================================================
with tab5:
    st.header("📈 Provincial Trends in Mortality Levels (qx)")
    if not df_qx.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Settings")
            provinces = sorted(df_qx['level'].unique())
            selected_province = st.selectbox("Select Province", provinces, index=provinces.index("İstanbul") if "İstanbul" in provinces else 0)
            selected_sex_prov_qx = st.radio("Select Sex", df_qx['sex'].unique(), index=0, key="prov_qx_sex")

        with col2:
            filtered_qx = df_qx[(df_qx['level'] == selected_province) & (df_qx['sex'] == selected_sex_prov_qx)].sort_values("year")
            if not filtered_qx.empty:
                fig_line = px.line(
                    filtered_qx, x="year", y="qx", color="rate_label", markers=True,
                    title=f"Mortality Trends in {selected_province} ({selected_sex_prov_qx})",
                    labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                    color_discrete_map={
                        "Neonatal Mortality (q28d)": "#2ca02c",
                        "Infant Mortality (q12m)": "#1f77b4",
                        "Under-5 Mortality (q5y)": "#d62728"
                    }
                )
                fig_line.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_line, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                safe_prov_name = selected_province.replace(" ", "_").lower()
                show_data_expander(filtered_qx, f"provincial_qx_{safe_prov_name}_{selected_sex_prov_qx}.csv")
            else:
                st.warning("No data available.")
    else:
        st.error("Provincial qx data not found.")

# =============================================================================
# TAB 6: PROVINCIAL MAPS (k)
# =============================================================================
with tab6:
    st.header("🗺️ Spatial Patterns of Mortality (Provincial k)")
    if not df_k.empty:
        m_col1, m_col2 = st.columns([1, 4])
        with m_col1:
            st.markdown("### Map Settings")
            years = sorted(df_k['year'].unique())
            selected_year_k = st.select_slider("Select Year", options=years, value=years[-1] if years else 2023, key="prov_map_y")
            selected_sex_k = st.radio("Select Sex", df_k['sex'].unique(), index=0, key="prov_map_sex")
            st.markdown("---")
            show_prov_names = st.checkbox("Show Province Names", value=False)
            show_values = st.checkbox("Show k Values", value=False)

        with m_col2:
            filtered_k = df_k[(df_k['year'] == selected_year_k) & (df_k['sex'] == selected_sex_k)]
            if not filtered_k.empty:
                fig_map = px.choropleth(
                    filtered_k, geojson=turkey_geojson, locations='level', featureidkey="properties.name",
                    color='k', color_continuous_scale="RdBu_r", range_color=(-2.0, 2.0),
                    title=f"Provincial k Pattern in {selected_year_k} ({selected_sex_k})", hover_data={'level': True, 'k': ':.2f'}
                )
                bg_trace = go.Choropleth(
                    geojson=turkey_geojson, locations=valid_map_names, featureidkey="properties.name",
                    z=[1] * len(valid_map_names), colorscale=[[0, '#dcedc8'], [1, '#dcedc8']],
                    showscale=False, marker_line_width=0.5, marker_line_color="white", hoverinfo='skip'
                )
                fig_map.add_trace(bg_trace)
                fig_map.data = (fig_map.data[-1],) + fig_map.data[:-1]

                if show_prov_names or show_values:
                    map_labels = []
                    data_dict = dict(zip(filtered_k['level'], filtered_k['k']))
                    for prov_name in valid_map_names:
                        if prov_name in province_centroids:
                            lat, lon = province_centroids[prov_name]
                            label_text = ""
                            if show_prov_names: label_text += f"<b>{prov_name}</b>"
                            if show_values and prov_name in data_dict:
                                if show_prov_names: label_text += "<br>"
                                label_text += f"{data_dict[prov_name]:.2f}"
                            if label_text:
                                map_labels.append(dict(lat=lat, lon=lon, text=label_text))
                    labels_df = pd.DataFrame(map_labels)
                    if not labels_df.empty:
                        fig_map.add_trace(go.Scattergeo(lon=labels_df['lon'], lat=labels_df['lat'], text=labels_df['text'], mode='text', textfont=dict(size=9, color="black")))

                fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig_map, use_container_width=True)
                
                # DATA VIEW & DOWNLOAD EKLENDİ
                show_data_expander(filtered_k, f"provincial_map_k_{selected_year_k}_{selected_sex_k}.csv")
            else:
                st.warning("No data available.")
    else:
        st.error("Provincial k data not found.")