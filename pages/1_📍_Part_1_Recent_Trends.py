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
    page_title="Part 1: Recent Trends (2009-2023)",
    page_icon="📍",
    layout="wide"
)

st.title("📍 Part 1: Provincial Mortality Analysis (2009–2023)")
st.markdown("Detailed analysis of mortality trends and patterns for all **81 provinces**.")


# -----------------------------------------------------------------------------
# 2. VERİ YÜKLEME (DATA KLASÖRÜNDEN)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Dosya yolları 'data/' klasörüne yönlendirildi
    # İster CSV ister Excel olsun okumaya çalışacak

    # 1. qx Verisi
    try:
        df_qx = pd.read_csv("data/part1_qx.csv")
    except:
        try:
            df_qx = pd.read_excel("data/part1_qx.xlsx")
        except:
            st.error("Data file 'part1_qx' not found in 'data/' folder.")
            st.stop()

    # 2. k Verisi
    try:
        df_k = pd.read_csv("data/part1_ks.csv")
    except:
        try:
            df_k = pd.read_excel("data/part1_ks.xlsx")
        except:
            st.error("Data file 'part1_ks' not found in 'data/' folder.")
            st.stop()

    # --- ORTAK TEMİZLİK ---
    for df in [df_qx, df_k]:
        df['level'] = df['level'].str.title().str.strip()
        df['sex'] = df['sex'].str.title().str.strip()

    # Türkçe Karakter Haritalaması
    corrections = {
        "Istanbul": "İstanbul", "Izmir": "İzmir",
        "Afyon": "Afyonkarahisar", "Afyonkarahisar": "Afyonkarahisar",
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

    df_qx['level'] = df_qx['level'].replace(corrections)
    df_k['level'] = df_k['level'].replace(corrections)

    # qx Etiketleri
    rate_map = {
        "q28": "Neonatal Mortality (q28d)",
        "IMR": "Infant Mortality (q12m)",
        "U5MR": "Under-5 Mortality (q5y)"
    }
    df_qx['rate_label'] = df_qx['rate'].map(rate_map).fillna(df_qx['rate'])

    return df_qx, df_k


# -----------------------------------------------------------------------------
# 3. HARİTA KAYNAKLARI (DATA KLASÖRÜNDEN)
# -----------------------------------------------------------------------------
@st.cache_data
def load_map_resources():
    # Harita dosyası data klasöründe aranıyor
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
        if feature['geometry']['type'] == 'MultiPolygon':
            coords = coords[0][0]
        else:
            coords = coords[0]
        lon = np.mean([p[0] for p in coords])
        lat = np.mean([p[1] for p in coords])
        centroids[name] = (lat, lon)

    return geojson, centroids, valid_provinces


try:
    df_qx, df_k = load_data()
    turkey_geojson, province_centroids, valid_map_names = load_map_resources()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 4. ARAYÜZ
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["📈 Mortality Levels (qx)", "🗺️ Mortality Patterns (k)"])

# ... TAB 1 AYNI (Değişiklik yok) ...
with tab1:
    st.header("📈 Trends in Mortality Levels")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### Settings")
        provinces = sorted(df_qx['level'].unique())
        selected_province = st.selectbox("Select Province", provinces,
                                         index=provinces.index("İstanbul") if "İstanbul" in provinces else 0)
        sex_options = df_qx['sex'].unique()
        selected_sex_qx = st.radio("Select Sex", sex_options, index=0, key="qx_sex")

    with col2:
        filtered_qx = df_qx[
            (df_qx['level'] == selected_province) &
            (df_qx['sex'] == selected_sex_qx)
            ].sort_values("year")

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

            with st.expander("View Underlying Data"):
                st.dataframe(filtered_qx[['year', 'rate_label', 'qx']], use_container_width=True)
                csv_qx = filtered_qx.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv_qx, f"{selected_province}_{selected_sex_qx}_qx.csv", "text/csv")
        else:
            st.warning("No data available.")

# ... TAB 2 AYNI (Değişiklik yok) ...
with tab2:
    st.header("🗺️ Spatial Patterns of Mortality (k parameter)")
    m_col1, m_col2 = st.columns([1, 4])

    with m_col1:
        st.markdown("### Map Settings")
        years = sorted(df_k['year'].unique())
        selected_year_k = st.select_slider("Select Year", options=years, value=2023)
        selected_sex_k = st.radio("Select Sex", df_k['sex'].unique(), index=0, key="k_sex")
        st.markdown("---")
        show_prov_names = st.checkbox("Show Province Names", value=False)
        show_values = st.checkbox("Show k Values", value=False)

    with m_col2:
        filtered_k = df_k[
            (df_k['year'] == selected_year_k) &
            (df_k['sex'] == selected_sex_k)
            ]

        # 1. DATA LAYER
        fig_map = px.choropleth(
            filtered_k,
            geojson=turkey_geojson,
            locations='level',
            featureidkey="properties.name",
            color='k',
            color_continuous_scale="RdBu_r",
            range_color=(-2.0, 2.0),
            title=f"Mortality Pattern (k) in {selected_year_k} ({selected_sex_k})",
            hover_data={'level': True, 'k': ':.2f'}
        )

        # 2. MISSING DATA LAYER (GREEN)
        bg_trace = go.Choropleth(
            geojson=turkey_geojson,
            locations=valid_map_names,
            featureidkey="properties.name",
            z=[1] * len(valid_map_names),
            colorscale=[[0, '#dcedc8'], [1, '#dcedc8']],
            showscale=False,
            marker_line_width=0.5,
            marker_line_color="white",
            hoverinfo='skip'
        )
        fig_map.add_trace(bg_trace)
        fig_map.data = (fig_map.data[-1],) + fig_map.data[:-1]

        # 3. LABELS
        if show_prov_names or show_values:
            map_labels = []
            data_dict = dict(zip(filtered_k['level'], filtered_k['k']))
            for prov_name in valid_map_names:
                if prov_name in province_centroids:
                    lat, lon = province_centroids[prov_name]
                    label_text = ""
                    has_data = prov_name in data_dict
                    if show_prov_names:
                        label_text += f"<b>{prov_name}</b>"
                    if show_values and has_data:
                        if show_prov_names: label_text += "<br>"
                        label_text += f"{data_dict[prov_name]:.2f}"
                    if label_text:
                        map_labels.append(dict(lat=lat, lon=lon, text=label_text))

            labels_df = pd.DataFrame(map_labels)
            if not labels_df.empty:
                fig_map.add_trace(go.Scattergeo(
                    lon=labels_df['lon'], lat=labels_df['lat'], text=labels_df['text'],
                    mode='text', textfont=dict(size=9, color="black")
                ))

        # 4. WORLD BACKGROUND
        fig_map.update_geos(
            fitbounds="locations", visible=False, showland=True,
            landcolor="#f0f0f0", showcountries=True, countrycolor="white",
            showocean=False, showlakes=False
        )
        fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=700)
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