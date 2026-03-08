import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# 2. YARDIMCI FONKSİYONLAR & SÖZLÜKLER
# -----------------------------------------------------------------------------
# Türkçe il isimleri sözlüğü (R uyumlu isimleri gerçek Türkçe isimlere çevirir)
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
# 3. VERİ YÜKLEME
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
            # Bölge adlarını title formatına getiriyoruz (WEST ANATOLIA -> West Anatolia)
            df['level'] = df['level'].str.strip().str.lower().replace(region_map).str.title()
        if not df.empty and 'sex' in df.columns:
            df['sex'] = df['sex'].str.title().str.strip()

    if not df_nat_k.empty and 'sex' in df_nat_k.columns:
        df_nat_k['sex'] = df_nat_k['sex'].str.title().str.strip()

    for df in [df_qx, df_k]:
        if not df.empty and 'level' in df.columns:
            df['level'] = df['level'].str.title().str.strip()
            df['level'] = df['level'].replace(PROVINCE_CORRECTIONS)
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
        st.error(f"Map file '{file_name}' not found. Map features will be disabled.")
        return None, {}, []

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
# 4. YENİ SIDEBAR (SOL MENÜ) NAVİGASYON SİSTEMİ
# -----------------------------------------------------------------------------
st.sidebar.title("📌 Navigation")
st.sidebar.markdown("Select the geographic level of analysis:")

page = st.sidebar.radio("", [
    "🇹🇷 National Level",
    "🗺️ Regional Level (NUTS-1)",
    "🏙️ Provincial Level"
])

st.sidebar.markdown("---")
st.sidebar.info("Use the tabs on the main screen to switch between trends, maps, and undercoverage analysis.")

# =============================================================================
# SAYFA 1: NATIONAL LEVEL
# =============================================================================
if page == "🇹🇷 National Level":
    tab1, tab2 = st.tabs(["📉 Trends (qx)", "🧩 Patterns (k)"])

    with tab1:
        st.header("🇹🇷 National Trends in Mortality Levels (qx)")
        if not df_nat_qx.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                sex_opts = df_nat_qx['sex'].unique()
                selected_sex_nat_qx = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="nat_qx_sex")

            with col2:
                filtered_nat_qx = df_nat_qx[df_nat_qx['sex'] == selected_sex_nat_qx].sort_values("year")
                if not filtered_nat_qx.empty:
                    fig_nat_qx = px.line(
                        filtered_nat_qx, x="year", y="qx", color="rate_label", markers=True,
                        title=f"National Mortality Trends ({selected_sex_nat_qx})",
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig_nat_qx.update_layout(height=500, xaxis=dict(dtick=1))
                    st.plotly_chart(fig_nat_qx, use_container_width=True)
                    
                    clean_nat_qx = filtered_nat_qx[['year', 'sex', 'rate_label', 'qx']].rename(columns={'year': 'Year', 'sex': 'Sex', 'rate_label': 'Indicator', 'qx': 'Probability_of_Dying (qx)'})
                    show_data_expander(clean_nat_qx, f"national_qx_{selected_sex_nat_qx}.csv")
                else:
                    st.warning("No data available.")

    with tab2:
        st.header("🇹🇷 National Trend of Mortality Pattern (k parameter)")
        if not df_nat_k.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                available_sexes = df_nat_k['sex'].unique()
                view_mode = st.radio("View Mode", ["Single Sex", "Compare All Sexes"], index=1, key="nat_k_mode")
                
                if view_mode == "Single Sex":
                    sel_sex_nat_k = st.selectbox("Select Sex", available_sexes, index=get_total_index(available_sexes), key="nat_k_sex")
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
                    
                    clean_nat_k = df_plot_k[['year', 'sex', 'k']].rename(columns={'year': 'Year', 'sex': 'Sex', 'k': 'Shape_Parameter_k'})
                    file_name_k = f"national_k_{sel_sex_nat_k}.csv" if view_mode == "Single Sex" else "national_k_all.csv"
                    show_data_expander(clean_nat_k, file_name_k)
                else:
                    st.warning("No data to plot.")

# =============================================================================
# SAYFA 2: REGIONAL LEVEL
# =============================================================================
elif page == "🗺️ Regional Level (NUTS-1)":
    tab1, tab2, tab3 = st.tabs(["📉 Trends (qx)", "🗺️ Maps (k)", "⚠️ Undercoverage Analysis"])

    with tab1:
        st.header("🗺️ Regional Trends in Mortality Levels (qx)")
        if not df_reg_qx.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                regions = sorted(df_reg_qx['level'].unique())
                selected_region = st.selectbox("Select Region (NUTS-1)", regions)
                sex_opts = df_reg_qx['sex'].unique()
                selected_sex_reg_qx = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="reg_qx_sex")

            with col2:
                filtered_reg_qx = df_reg_qx[(df_reg_qx['level'] == selected_region) & (df_reg_qx['sex'] == selected_sex_reg_qx)].sort_values("year")
                if not filtered_reg_qx.empty:
                    fig_reg_qx = px.line(
                        filtered_reg_qx, x="year", y="qx", color="rate_label", markers=True,
                        title=f"Mortality Trends in {selected_region} ({selected_sex_reg_qx})",
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig_reg_qx.update_layout(height=500, xaxis=dict(dtick=1))
                    st.plotly_chart(fig_reg_qx, use_container_width=True)
                    
                    clean_reg_qx = filtered_reg_qx[['year', 'level', 'sex', 'rate_label', 'qx']].rename(columns={'year': 'Year', 'level': 'Region', 'sex': 'Sex', 'rate_label': 'Indicator', 'qx': 'Probability_of_Dying (qx)'})
                    show_data_expander(clean_reg_qx, f"regional_qx_{selected_region}_{selected_sex_reg_qx}.csv")
                else:
                    st.warning("No data available.")

    with tab2:
        st.header("🗺️ Regional Mortality Maps (NUTS-1 k parameter)")
        if not df_reg_k.empty and turkey_geojson:
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
                r_years = sorted(df_reg_k['year'].unique())
                selected_year_reg = st.select_slider("Select Year", options=r_years, value=r_years[-1] if r_years else 2023, key="reg_map_y")
                sex_opts = df_reg_k['sex'].unique()
                selected_sex_reg = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="reg_map_sex")
                show_reg_labels = st.checkbox("Show Region Names", value=True)

            with r_col2:
                filtered_reg_map = map_df[(map_df['year'] == selected_year_reg) & (map_df['sex'] == selected_sex_reg)]
                if not filtered_reg_map.empty:
                    unique_reg = filtered_reg_map[['region_name', 'k']].drop_duplicates()
                    sc1, sc2, sc3 = st.columns(3)
                    
                    nat_val_str = "N/A"
                    if not df_nat_k.empty:
                        nat_df = df_nat_k[(df_nat_k['year'] == selected_year_reg) & (df_nat_k['sex'] == selected_sex_reg)]
                        if not nat_df.empty: nat_val_str = f"{nat_df['k'].values[0]:.3f}"
                    sc1.metric("🇹🇷 National Average (k)", nat_val_str)
                    
                    if not unique_reg.empty:
                        max_idx = unique_reg['k'].idxmax()
                        sc2.metric(f"📈 Highest: {unique_reg.loc[max_idx, 'region_name']}", f"{unique_reg.loc[max_idx, 'k']:.3f}")
                        min_idx = unique_reg['k'].idxmin()
                        sc3.metric(f"📉 Lowest: {unique_reg.loc[min_idx, 'region_name']}", f"{unique_reg.loc[min_idx, 'k']:.3f}")
                    
                    st.markdown("<br>", unsafe_allow_html=True) 
                    
                    fig_reg_map = px.choropleth(
                        filtered_reg_map, geojson=turkey_geojson, locations='province_name', featureidkey="properties.name",
                        color='k', color_continuous_scale="RdBu_r", range_color=(-2.0, 2.0), hover_name='region_name',
                        hover_data={'province_name': False, 'k': ':.2f'}, title=f"NUTS1 Mortality Pattern in {selected_year_reg} ({selected_sex_reg})"
                    )
                    fig_reg_map.update_traces(marker_line_width=0, marker_opacity=1.0)

                    if show_reg_labels:
                        labels = []
                        for _, row in unique_reg.iterrows():
                            r_name, k_val = row['region_name'], row['k']
                            lbl_text = f"<b>{r_name}</b><br>{k_val:.2f}" if not pd.isna(k_val) else f"<b>{r_name}</b>"
                            if r_name in region_centroids:
                                labels.append(dict(lat=region_centroids[r_name][0], lon=region_centroids[r_name][1], text=lbl_text))

                        lbl_df = pd.DataFrame(labels)
                        if not lbl_df.empty:
                            fig_reg_map.add_trace(go.Scattergeo(lon=lbl_df['lon'], lat=lbl_df['lat'], text=lbl_df['text'], mode='text', textfont=dict(size=10, color="black")))

                    fig_reg_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                    fig_reg_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                    st.plotly_chart(fig_reg_map, use_container_width=True)
                    
                    clean_reg_map = filtered_reg_map[['year', 'region_name', 'sex', 'k']].drop_duplicates().rename(columns={'year': 'Year', 'region_name': 'Region', 'sex': 'Sex', 'k': 'Shape_Parameter_k'})
                    show_data_expander(clean_reg_map, f"regional_map_k_{selected_year_reg}.csv")

    with tab3:
        st.header("⚠️ Regional Undercoverage Analysis")
        try:
            df_uc = pd.read_csv("data/undercoverage_all_regions.csv")
            # Bölge adlarını büyük harfle düzenliyoruz (WEST ANATOLIA -> West Anatolia)
            df_uc['level'] = df_uc['level'].astype(str).str.title().str.strip()
            
            qx_col = 'qx'
            for col in df_uc.columns:
                if col.strip().lower() == 'qx' or col.strip() == 'Observed_q(28d)' or col.strip() == 'q28_5':
                    qx_col = col; break

            if qx_col not in df_uc.columns:
                st.error("Gözlemlenen oran sütunu bulunamadı.")
            else:
                df_uc['rel_uc'] = (df_uc[qx_col] / df_uc['p.qx']) * 100 
                df_uc['rel_uc_up'] = (df_uc[qx_col] / df_uc['p.qx_m']) * 100
                df_uc['rel_uc_low'] = (df_uc[qx_col] / df_uc['p.qx_p']) * 100
                
                df_uc['uc'] = df_uc['deaths_28'] / (df_uc['rel_uc'] / 100) - df_uc['deaths_28']
                df_uc['uc_up'] = df_uc['deaths_28'] / (df_uc['rel_uc_up'] / 100) - df_uc['deaths_28']
                df_uc['uc_low'] = df_uc['deaths_28'] / (df_uc['rel_uc_low'] / 100) - df_uc['deaths_28']

                df_uc_plot = df_uc[df_uc['age_d'] == 21].copy()

                col1, col2 = st.columns([1, 3])
                with col1:
                    regions_uc = sorted(df_uc_plot['level'].unique())
                    selected_reg_uc = st.selectbox("Select Region for Analysis", regions_uc, key="uc_region")
                
                with col2:
                    filtered_uc = df_uc_plot[df_uc_plot['level'] == selected_reg_uc].sort_values("year")
                    
                    if not filtered_uc.empty:
                        sub_tab_a, sub_tab_b, sub_tab_c = st.tabs(["📊 Panel A: Probability of Dying", "📉 Panel B: Undercoverage (%)", "⚠️ Panel C: Underreported Deaths"])

                        with sub_tab_a:
                            fig_a = go.Figure()
                            fig_a.add_trace(go.Scatter(x=filtered_uc['year'], y=filtered_uc['p.qx'], mode='lines', name='Predicted', line=dict(dash='dash', color='#1f77b4', width=3)))
                            fig_a.add_trace(go.Scatter(x=filtered_uc['year'], y=filtered_uc[qx_col], mode='lines', name='Observed', line=dict(color='#d62728', width=3)))
                            fig_a.add_trace(go.Scatter(
                                x=filtered_uc['year'].tolist() + filtered_uc['year'].tolist()[::-1],
                                y=filtered_uc['p.qx_m'].tolist() + filtered_uc['p.qx_p'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(31, 119, 180, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_a.update_layout(height=550, hovermode="x unified", title_text=f"Panel A: Probability of Dying q(28d) for {selected_reg_uc}")
                            fig_a.update_xaxes(dtick=2)
                            st.plotly_chart(fig_a, use_container_width=True)

                        with sub_tab_b:
                            fig_b = go.Figure()
                            fig_b.add_trace(go.Scatter(x=filtered_uc['year'], y=filtered_uc['rel_uc'], mode='lines+markers', name='Undercoverage', line=dict(color='#ff7f0e', width=3)))
                            fig_b.add_trace(go.Scatter(
                                x=filtered_uc['year'].tolist() + filtered_uc['year'].tolist()[::-1],
                                y=filtered_uc['rel_uc_up'].tolist() + filtered_uc['rel_uc_low'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(255, 127, 14, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_b.add_hline(y=100, line_color="#d62728", line_width=2, line_dash="dot", opacity=0.8, annotation_text="100% (Perfect Coverage)")
                            fig_b.update_layout(height=550, hovermode="x unified", title_text=f"Panel B: Undercoverage (%) for {selected_reg_uc}")
                            fig_b.update_xaxes(dtick=2)
                            st.plotly_chart(fig_b, use_container_width=True)

                        with sub_tab_c:
                            fig_c = go.Figure()
                            fig_c.add_trace(go.Scatter(x=filtered_uc['year'], y=filtered_uc['uc'], mode='lines+markers', name='Underreported Deaths', line=dict(color='#9467bd', width=3)))
                            fig_c.add_trace(go.Scatter(
                                x=filtered_uc['year'].tolist() + filtered_uc['year'].tolist()[::-1],
                                y=filtered_uc['uc_up'].tolist() + filtered_uc['uc_low'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(148, 103, 189, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_c.add_hline(y=0, line_color="#d62728", line_width=2, line_dash="dot", opacity=0.8, annotation_text="0 (No Underreporting)")
                            fig_c.update_layout(height=550, hovermode="x unified", title_text=f"Panel C: Absolute Number of Underreported Deaths for {selected_reg_uc}")
                            fig_c.update_xaxes(dtick=2)
                            st.plotly_chart(fig_c, use_container_width=True)

                        st.markdown("---")
                        clean_uc = filtered_uc[['year', 'level', qx_col, 'p.qx', 'p.qx_p', 'p.qx_m', 'rel_uc', 'rel_uc_low', 'rel_uc_up', 'uc', 'uc_low', 'uc_up']].copy()
                        num_cols = clean_uc.select_dtypes(include=['float64', 'float32']).columns
                        clean_uc[num_cols] = clean_uc[num_cols].round(4)
                        clean_uc.columns = ['Year', 'Region', 'Observed_q(28d)', 'Predicted_q(28d)', 'Pred_Lower_Bound', 'Pred_Upper_Bound', 'Undercoverage_%', 'Undercoverage_Lower_%', 'Undercoverage_Upper_%', 'Underreported_Deaths', 'Underreported_Lower', 'Underreported_Upper']
                        show_data_expander(clean_uc, f"regional_undercoverage_{selected_reg_uc}.csv")

        except FileNotFoundError:
            st.error("Lütfen önce offline R kodunu çalıştırarak 'data/undercoverage_all_regions.csv' dosyasını oluşturun.")


# =============================================================================
# SAYFA 3: PROVINCIAL LEVEL
# =============================================================================
elif page == "🏙️ Provincial Level":
    tab1, tab2, tab3 = st.tabs(["📉 Trends (qx)", "🗺️ Maps (k)", "⚠️ Undercoverage Analysis"])

    with tab1:
        st.header("📈 Provincial Trends in Mortality Levels (qx)")
        if not df_qx.empty:
            col1, col2 = st.columns([1, 3])
            with col1:
                provinces = sorted(df_qx['level'].unique())
                selected_province = st.selectbox("Select Province", provinces, index=provinces.index("İstanbul") if "İstanbul" in provinces else 0)
                sex_opts = df_qx['sex'].unique()
                selected_sex_prov_qx = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="prov_qx_sex")

            with col2:
                filtered_qx = df_qx[(df_qx['level'] == selected_province) & (df_qx['sex'] == selected_sex_prov_qx)].sort_values("year")
                if not filtered_qx.empty:
                    fig_line = px.line(
                        filtered_qx, x="year", y="qx", color="rate_label", markers=True,
                        title=f"Mortality Trends in {selected_province} ({selected_sex_prov_qx})",
                        labels={"qx": "Probability of Dying", "rate_label": "Indicator", "year": "Year"},
                        color_discrete_map={"Neonatal Mortality (q28d)": "#2ca02c", "Infant Mortality (q12m)": "#1f77b4", "Under-5 Mortality (q5y)": "#d62728"}
                    )
                    fig_line.update_layout(height=500, xaxis=dict(dtick=1))
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                    clean_prov_qx = filtered_qx[['year', 'level', 'sex', 'rate_label', 'qx']].rename(columns={'year': 'Year', 'level': 'Province', 'sex': 'Sex', 'rate_label': 'Indicator', 'qx': 'Probability_of_Dying (qx)'})
                    show_data_expander(clean_prov_qx, f"provincial_qx_{selected_province}.csv")
                else:
                    st.warning("No data available.")

    with tab2:
        st.header("🗺️ Spatial Patterns of Mortality (Provincial k)")
        if not df_k.empty and turkey_geojson:
            m_col1, m_col2 = st.columns([1, 4])
            with m_col1:
                years = sorted(df_k['year'].unique())
                selected_year_k = st.select_slider("Select Year", options=years, value=years[-1] if years else 2023, key="prov_map_y")
                sex_opts = df_k['sex'].unique()
                selected_sex_k = st.radio("Select Sex", sex_opts, index=get_total_index(sex_opts), key="prov_map_sex")
                st.markdown("---")
                show_prov_names = st.checkbox("Show Province Names", value=False)
                show_values = st.checkbox("Show k Values", value=False)

            with m_col2:
                filtered_k = df_k[(df_k['year'] == selected_year_k) & (df_k['sex'] == selected_sex_k)]
                if not filtered_k.empty:
                    sc1, sc2, sc3 = st.columns(3)
                    nat_val_str = "N/A"
                    if not df_nat_k.empty:
                        nat_df = df_nat_k[(df_nat_k['year'] == selected_year_k) & (df_nat_k['sex'] == selected_sex_k)]
                        if not nat_df.empty: nat_val_str = f"{nat_df['k'].values[0]:.3f}"
                    sc1.metric("🇹🇷 National Average (k)", nat_val_str)
                    
                    max_idx = filtered_k['k'].idxmax()
                    sc2.metric(f"📈 Highest: {filtered_k.loc[max_idx, 'level']}", f"{filtered_k.loc[max_idx, 'k']:.3f}")
                    min_idx = filtered_k['k'].idxmin()
                    sc3.metric(f"📉 Lowest: {filtered_k.loc[min_idx, 'level']}", f"{filtered_k.loc[min_idx, 'k']:.3f}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)

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
                                if label_text: map_labels.append(dict(lat=lat, lon=lon, text=label_text))
                        labels_df = pd.DataFrame(map_labels)
                        if not labels_df.empty:
                            fig_map.add_trace(go.Scattergeo(lon=labels_df['lon'], lat=labels_df['lat'], text=labels_df['text'], mode='text', textfont=dict(size=9, color="black")))

                    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="#f0f0f0")
                    fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                    st.plotly_chart(fig_map, use_container_width=True)
                    
                    clean_prov_k = filtered_k[['year', 'level', 'sex', 'k']].rename(columns={'year': 'Year', 'level': 'Province', 'sex': 'Sex', 'k': 'Shape_Parameter_k'})
                    show_data_expander(clean_prov_k, f"provincial_map_k_{selected_year_k}.csv")

    with tab3:
        st.header("🏙️ Provincial Undercoverage & Missing Deaths Analysis")
        try:
            df_prov_uc = pd.read_csv("data/undercoverage_all_provinces.csv")
            
            # İl isimlerini büyük/küçük harf formatına sokup, ardından gerçek Türkçe karakterli sözlüğe göre değiştiriyoruz.
            df_prov_uc['level'] = df_prov_uc['level'].astype(str).str.title().str.strip().replace(PROVINCE_CORRECTIONS)
            
            qx_col_prov = 'qx'
            for col in df_prov_uc.columns:
                if col.strip().lower() == 'qx' or col.strip() == 'Observed_q(28d)' or col.strip() == 'q28_5':
                    qx_col_prov = col; break

            if qx_col_prov not in df_prov_uc.columns:
                st.error("Gözlemlenen oran sütunu bulunamadı.")
            else:
                df_prov_uc['rel_uc'] = (df_prov_uc[qx_col_prov] / df_prov_uc['p.qx']) * 100 
                df_prov_uc['rel_uc_up'] = (df_prov_uc[qx_col_prov] / df_prov_uc['p.qx_m']) * 100
                df_prov_uc['rel_uc_low'] = (df_prov_uc[qx_col_prov] / df_prov_uc['p.qx_p']) * 100
                
                df_prov_uc['uc'] = df_prov_uc['deaths_28'] / (df_prov_uc['rel_uc'] / 100) - df_prov_uc['deaths_28']
                df_prov_uc['uc_up'] = df_prov_uc['deaths_28'] / (df_prov_uc['rel_uc_up'] / 100) - df_prov_uc['deaths_28']
                df_prov_uc['uc_low'] = df_prov_uc['deaths_28'] / (df_prov_uc['rel_uc_low'] / 100) - df_prov_uc['deaths_28']

                df_prov_plot = df_prov_uc[df_prov_uc['age_d'] == 21].copy()

                col1, col2 = st.columns([1, 3])
                with col1:
                    provinces_uc = sorted(df_prov_plot['level'].unique())
                    default_prov_idx = provinces_uc.index("Hatay") if "Hatay" in provinces_uc else 0
                    selected_prov_uc = st.selectbox("Select Province for Analysis", provinces_uc, index=default_prov_idx, key="uc_province")
                
                with col2:
                    filtered_prov_uc = df_prov_plot[df_prov_plot['level'] == selected_prov_uc].sort_values("year")
                    
                    if not filtered_prov_uc.empty:
                        sub_tab_pa, sub_tab_pb, sub_tab_pc = st.tabs(["📊 Panel A: Probability of Dying", "📉 Panel B: Undercoverage (%)", "⚠️ Panel C: Underreported Deaths"])

                        with sub_tab_pa:
                            fig_pa = go.Figure()
                            fig_pa.add_trace(go.Scatter(x=filtered_prov_uc['year'], y=filtered_prov_uc['p.qx'], mode='lines', name='Predicted', line=dict(dash='dash', color='#1f77b4', width=3)))
                            fig_pa.add_trace(go.Scatter(x=filtered_prov_uc['year'], y=filtered_prov_uc[qx_col_prov], mode='lines', name='Observed', line=dict(color='#d62728', width=3)))
                            fig_pa.add_trace(go.Scatter(
                                x=filtered_prov_uc['year'].tolist() + filtered_prov_uc['year'].tolist()[::-1],
                                y=filtered_prov_uc['p.qx_m'].tolist() + filtered_prov_uc['p.qx_p'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(31, 119, 180, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_pa.update_layout(height=550, hovermode="x unified", title_text=f"Panel A: Probability of Dying q(28d) for {selected_prov_uc}")
                            fig_pa.update_xaxes(dtick=2)
                            st.plotly_chart(fig_pa, use_container_width=True)

                        with sub_tab_pb:
                            fig_pb = go.Figure()
                            fig_pb.add_trace(go.Scatter(x=filtered_prov_uc['year'], y=filtered_prov_uc['rel_uc'], mode='lines+markers', name='Undercoverage', line=dict(color='#ff7f0e', width=3)))
                            fig_pb.add_trace(go.Scatter(
                                x=filtered_prov_uc['year'].tolist() + filtered_prov_uc['year'].tolist()[::-1],
                                y=filtered_prov_uc['rel_uc_up'].tolist() + filtered_prov_uc['rel_uc_low'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(255, 127, 14, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_pb.add_hline(y=100, line_color="#d62728", line_width=2, line_dash="dot", opacity=0.8, annotation_text="100% (Perfect Coverage)")
                            fig_pb.update_layout(height=550, hovermode="x unified", title_text=f"Panel B: Undercoverage (%) for {selected_prov_uc}")
                            fig_pb.update_xaxes(dtick=2)
                            st.plotly_chart(fig_pb, use_container_width=True)

                        with sub_tab_pc:
                            fig_pc = go.Figure()
                            fig_pc.add_trace(go.Scatter(x=filtered_prov_uc['year'], y=filtered_prov_uc['uc'], mode='lines+markers', name='Underreported Deaths', line=dict(color='#9467bd', width=3)))
                            fig_pc.add_trace(go.Scatter(
                                x=filtered_prov_uc['year'].tolist() + filtered_prov_uc['year'].tolist()[::-1],
                                y=filtered_prov_uc['uc_up'].tolist() + filtered_prov_uc['uc_low'].tolist()[::-1],
                                fill='toself', fillcolor='rgba(148, 103, 189, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty Interval'
                            ))
                            fig_pc.add_hline(y=0, line_color="#d62728", line_width=2, line_dash="dot", opacity=0.8, annotation_text="0 (No Underreporting)")
                            fig_pc.update_layout(height=550, hovermode="x unified", title_text=f"Panel C: Absolute Number of Underreported Deaths for {selected_prov_uc}")
                            fig_pc.update_xaxes(dtick=2)
                            st.plotly_chart(fig_pc, use_container_width=True)

                        st.markdown("---")
                        clean_prov_uc = filtered_prov_uc[['year', 'level', qx_col_prov, 'p.qx', 'p.qx_p', 'p.qx_m', 'rel_uc', 'rel_uc_low', 'rel_uc_up', 'uc', 'uc_low', 'uc_up']].copy()
                        num_cols = clean_prov_uc.select_dtypes(include=['float64', 'float32']).columns
                        clean_prov_uc[num_cols] = clean_prov_uc[num_cols].round(4)
                        clean_prov_uc.columns = ['Year', 'Province', 'Observed_q(28d)', 'Predicted_q(28d)', 'Pred_Lower_Bound', 'Pred_Upper_Bound', 'Undercoverage_%', 'Undercoverage_Lower_%', 'Undercoverage_Upper_%', 'Underreported_Deaths', 'Underreported_Lower', 'Underreported_Upper']
                        show_data_expander(clean_prov_uc, f"provincial_undercoverage_{selected_prov_uc}.csv")

        except FileNotFoundError:
            st.error("Lütfen önce offline R kodunu çalıştırarak 'data/undercoverage_all_provinces.csv' dosyasını oluşturun.")