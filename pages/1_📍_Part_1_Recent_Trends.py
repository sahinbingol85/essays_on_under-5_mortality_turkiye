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
# 2. YARDIMCI FONKSİYONLAR (BÖLGESEL HARİTA İÇİN)
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

# -----------------------------------------------------------------------------
# 3. VERİ YÜKLEME (DATA KLASÖRÜNDEN)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1. İl qx Verisi
    try:
        df_qx = pd.read_csv("data/part1_qx.csv")
    except:
        try:
            df_qx = pd.read_excel("data/part1_qx.xlsx")
        except:
            df_qx = pd.DataFrame()

    # 2. İl k Verisi
    try:
        df_k = pd.read_csv("data/part1_ks.csv")
    except:
        try:
            df_k = pd.read_excel("data/part1_ks.xlsx")
        except:
            df_k = pd.DataFrame()
        
    # 3. Bölgesel (Regional) k Verisi
    try:
        df_reg_k = pd.read_csv("data/part1_ks_regional.csv")
    except:
        try:
            df_reg_k = pd.read_excel("data/part1_ks_regional.xlsx")
        except:
            df_reg_k = pd.DataFrame()

    # 4. Ulusal (National) k Verisi
    try:
        df_nat_k = pd.read_csv("data/part1_ks_national.csv")
    except:
        try:
            df_nat_k = pd.read_excel("data/part1_ks_national.xlsx")
        except:
            df_nat_k = pd.DataFrame()

    # --- VERİ TEMİZLİĞİ VE STANDARTLAŞTIRMA ---
    
    # Türkçe Karakter Haritalaması (Sadece İller İçin)
    corrections = {
        "Istanbul": "İstanbul", "Izmir": "İzmir", "Afyon": "Afyonkarahisar",
        "Agri": "Ağrı", "Canakkale": "Çanakkale", "Cankiri": "Çankırı",
        "Corum": "Çorum", "Diyarbakir": "Diyarbakır", "Eskisehir": "Eskişehir",
        "Gumushane": "Gümüşhane", "Hakkari": "Hakkâri", "Kahramanmaras": "Kahramanmaraş",
        "Kirklareli": "Kırklareli", "Kirsehir": "Kırşehir", "Kutahya": "Kütahya",
        "Mugla": "Muğla", "Mus": "Muş", "Nevsehir": "Nevşehir", "Nigde": "Niğde",
        "Sanliurfa": "Şanlıurfa", "Tekirdag": "Tekirdağ", "Usak": "Uşak",
        "Balikesir": "Balıkesir", "Bingol": "Bingöl", "Adiyaman": "Adıyaman",
        "Elazig": "Elazığ", "Gaziantep": "Gaziantep", "Duzce": "Düzce",
        "Igdir": "Iğdır", "Sirnak": "Şırnak", "Bartin": "Bartın", "Karabuk": "Karabük",
        "Zonguldak": "Zonguldak", "Mersin": "Mersin", "Icel": "Mersin"
    }

    # İl Verileri Temizliği
    for df in [df_qx, df_k]:
        if not df.empty:
            if 'level' in df.columns:
                df['level'] = df['level'].str.title().str.strip()
                df['level'] = df['level'].replace(corrections)
            if 'sex' in df.columns:
                df['sex'] = df['sex'].str.title().str.strip()

    # qx Etiketleri
    if not df_qx.empty:
        rate_map = {
            "q28": "Neonatal Mortality (q28d)",
            "IMR": "Infant Mortality (q12m)",
            "U5MR": "Under-5 Mortality (q5y)"
        }
        df_qx['rate_label'] = df_qx['rate'].map(rate_map).fillna(df_qx['rate'])

    # Bölgesel Veri Temizliği (Özel İsim Eşleştirmesi)
    if not df_reg_k.empty:
        if 'level' in df_reg_k.columns:
            # Excel'deki ham isimleri, haritanın tanıdığı tam isimlere dönüştüren sözlük
            region_map = {
                'aegean': 'Aegean',
                'east_blacksea': 'East Black Sea',
                'east_marmara': 'East Marmara',
                'istanbul': 'Istanbul',
                'mediterranean': 'Mediterranean',
                'middle_anatolia': 'Central Anatolia',          # DÜZELTME BURADA
                'middle_east_anatolia': 'Central East Anatolia', # DÜZELTME BURADA
                'north_east_anatolia': 'Northeast Anatolia',     # DÜZELTME BURADA
                'south_east_anatolia': 'Southeast Anatolia',     # DÜZELTME BURADA
                'west_anatolia': 'West Anatolia',
                'west_blacksea': 'West Black Sea',               # DÜZELTME BURADA
                'west_marmara': 'West Marmara'
            }
            # Tüm isimleri güvenli bir şekilde küçük harfe çevirip eşleştiriyoruz
            df_reg_k['level'] = df_reg_k['level'].str.strip().str.lower().replace(region_map)

        if 'sex' in df_reg_k.columns:
            df_reg_k['sex'] = df_reg_k['sex'].str.title().str.strip()

    # Ulusal Veri Temizliği (female -> Female düzeltmesi)
    if not df_nat_k.empty:
        if 'sex' in df_nat_k.columns:
            df_nat_k['sex'] = df_nat_k['sex'].str.title().str.strip()

    return df_qx, df_k, df_reg_k, df_nat_k

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
    df_qx, df_k, df_reg_k, df_nat_k = load_data()
    turkey_geojson, province_centroids, valid_map_names = load_map_resources()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 4. ARAYÜZ (TABS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Provincial Trends (qx)", 
    "🗺️ Provincial Maps (k)", 
    "🗺️ Regional Maps (k)", 
    "🇹🇷 National Trend (k)"
])

# =============================================================================
# TAB 1: PROVINCIAL TRENDS (qx)
# =============================================================================
with tab1:
    st.header("📈 Trends in Mortality Levels")
    if not df_qx.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Settings")
            provinces = sorted(df_qx['level'].unique())
            selected_province = st.selectbox("Select Province", provinces, index=provinces.index("İstanbul") if "İstanbul" in provinces else 0)
            selected_sex_qx = st.radio("Select Sex", df_qx['sex'].unique(), index=0, key="qx_sex")

        with col2:
            filtered_qx = df_qx[(df_qx['level'] == selected_province) & (df_qx['sex'] == selected_sex_qx)].sort_values("year")
            if not filtered_qx.empty:
                fig_line = px.line(
                    filtered_qx, x="year", y="qx", color="rate_label", markers=True,
                    title=f"Mortality Trends in {selected_province} ({selected_sex_qx})",
                    labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                    color_discrete_map={
                        "Neonatal Mortality (q28d)": "#2ca02c",
                        "Infant Mortality (q12m)": "#1f77b4",
                        "Under-5 Mortality (q5y)": "#d62728"
                    }
                )
                fig_line.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("No data available.")
    else:
        st.error("Provincial qx data not found.")

# =============================================================================
# TAB 2: PROVINCIAL MAPS (k)
# =============================================================================
with tab2:
    st.header("🗺️ Spatial Patterns of Mortality (Provincial k)")
    if not df_k.empty:
        m_col1, m_col2 = st.columns([1, 4])
        with m_col1:
            st.markdown("### Map Settings")
            years = sorted(df_k['year'].unique())
            selected_year_k = st.select_slider("Select Year", options=years, value=years[-1] if years else 2023)
            selected_sex_k = st.radio("Select Sex", df_k['sex'].unique(), index=0, key="k_sex")
            st.markdown("---")
            show_prov_names = st.checkbox("Show Province Names", value=False)
            show_values = st.checkbox("Show k Values", value=False)

        with m_col2:
            filtered_k = df_k[(df_k['year'] == selected_year_k) & (df_k['sex'] == selected_sex_k)]
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
    else:
        st.error("Provincial k data not found.")

# =============================================================================
# TAB 3: REGIONAL MAPS (NUTS-1 k)
# =============================================================================
with tab3:
    st.header("🗺️ Regional Mortality Maps (NUTS-1 k parameter)")
    if not df_reg_k.empty:
        # Bölge Merkezlerini Hesapla
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
            selected_year_reg = st.select_slider("Select Year", options=r_years, value=r_years[-1] if r_years else 2023, key="reg_y")
            selected_sex_reg = st.radio("Select Sex", df_reg_k['sex'].unique(), index=0, key="reg_sex")
            show_reg_labels = st.checkbox("Show Region Names", value=True)

        with r_col2:
            filtered_reg_map = map_df[(map_df['year'] == selected_year_reg) & (map_df['sex'] == selected_sex_reg)]
            
            if not filtered_reg_map.empty:
                fig_reg_map = px.choropleth(
                    filtered_reg_map, geojson=turkey_geojson, locations='province_name', featureidkey="properties.name",
                    color='k', color_continuous_scale="RdBu_r", range_color=(-2.0, 2.0), hover_name='region_name',
                    hover_data={'province_name': False, 'k': ':.2f'}, title=f"NUTS1 Mortality Pattern in {selected_year_reg} ({selected_sex_reg})"
                )
                
                # Sınır çizgilerini kaldırarak blok görünümü ver
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
            else:
                st.warning("No regional data available for the selected year and sex.")
    else:
        st.error("Regional data (part1_ks_regional.csv/xlsx) not found. Please upload to the data folder.")

# =============================================================================
# TAB 4: NATIONAL TREND (k)
# =============================================================================
with tab4:
    st.header("🇹🇷 National Trend of Mortality Pattern (k parameter)")
    if not df_nat_k.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("### Chart Settings")
            available_sexes = df_nat_k['sex'].unique()
            # Kullanıcı "Total", "Male", "Female" seçebilir veya "All" diyerek hepsini görebilir
            view_mode = st.radio("View Mode", ["Single Sex", "Compare All Sexes"], index=1)
            
            if view_mode == "Single Sex":
                sel_sex_nat = st.selectbox("Select Sex", available_sexes)
                df_plot = df_nat_k[df_nat_k['sex'] == sel_sex_nat].sort_values("year")
            else:
                df_plot = df_nat_k.sort_values("year")
                
        with col2:
            if not df_plot.empty:
                fig_nat = px.line(
                    df_plot, x="year", y="k", color="sex" if view_mode == "Compare All Sexes" else None,
                    markers=True, title="National Trend of Shape Parameter (k) over Time",
                    labels={"k": "Shape Parameter (k)", "year": "Year", "sex": "Sex"}
                )
                
                # Sıfır çizgisi (modelin merkezi için) ekle
                fig_nat.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Standard Pattern (k=0)")
                
                fig_nat.update_layout(height=500, xaxis=dict(dtick=1))
                st.plotly_chart(fig_nat, use_container_width=True)
                
                with st.expander("View Data"):
                    st.dataframe(df_plot, use_container_width=True)
            else:
                st.warning("No data to plot.")
    else:
        st.error("National data (part1_ks_national.csv/xlsx) not found. Please upload to the data folder.")