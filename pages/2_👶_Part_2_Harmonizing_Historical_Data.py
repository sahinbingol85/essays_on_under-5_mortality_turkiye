import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Part 2: Harmonization of Historical Under-5 Mortality Data",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. MAIN TITLE
# -----------------------------------------------------------------------------
st.title("👶 Part 2: Harmonization of Historical Under-5 Mortality Data")
st.markdown("### Supplementary Materials for Appendix E, F, G, and H")

# -----------------------------------------------------------------------------
# 3. INTERNAL NAVIGATION (SUB-MENU)
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("Part 2 Sections")
selection = st.sidebar.radio(
    "Go to:",
    ["Overview",
     "Appendix E: Harmonized Mortality Data",
     "Appendix F: Derivation Process & Thresholds",
     "Appendix G: Zero-Age Tables & Graphs",
     "Appendix H: Demographic Convergence"]
)


# -----------------------------------------------------------------------------
# 4. DATA LOADING FUNCTION
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(file_name, header_arg=0):
    file_path = os.path.join("data", file_name)

    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_excel(file_path, header=header_arg)
        return df
    except Exception as e:
        st.error(f"Error reading file '{file_name}': {e}")
        return None


# =============================================================================
# SECTION: OVERVIEW
# =============================================================================
if selection == "Overview":
    st.info("👈 Please use the sidebar menu to navigate through Appendix E, F, G, and H.")

    st.header("About the Study")
    st.markdown("""
    ### **Objective**
    This study reconstructs Türkiye’s historical demographic trends by harmonizing fragmented archival records into a coherent longitudinal dataset. It addresses a critical gap in historical demography: the inconsistency between **mortality records** (often limited to administrative centers) and **census data** (covering the total population).

    ### **Key Methodological Contributions**
    1.  **Digitization & Standardization:** Fragmented historical mortality records from 1931 to 2008 were digitized and reclassified into a standardized **22-age category system**.

    2.  **Addressing the "Coverage Mismatch":**
        Historical mortality statistics were predominantly **urban-centric (Province and District Centers - PDC)**, while censuses covered the entire population. 

    3.  **Ratio-Based PDC Reconstruction:**
        To resolve this, the study introduces a novel **"Ratio-Based PDC Reconstruction Method"**. This approach isolates the true urban risk pools from census data and harmonizes them with mortality registries.

    4.  **Demographic Convergence:**
        Demonstrating how the rapid urbanization in Türkiye naturally expanded the statistical coverage of vital events, progressively mitigating historical data limitations over time.

    ### **Data Availability**
    The datasets provided here serve as the empirical foundation for this reconstruction.
    """)

# =============================================================================
# SECTION: APPENDIX E
# =============================================================================
elif selection == "Appendix E: Harmonized Mortality Data":
    st.header("📂 Appendix E: Harmonized Mortality Data")
    st.markdown("""
    This dataset contains the fully harmonized mortality statistics, standardized into comparable age groups.
    * **Coverage:** National Level (1950–2008) & Provincial Level (1931–2008)
    """)

    file_name = "part2_appendix_e.xlsx"
    df = load_data(file_name)

    if df is not None:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data (CSV)",
            data=csv,
            file_name="harmonized_mortality_appendix_e.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"⚠️ File '{file_name}' not found in 'data/' folder.")

# =============================================================================
# SECTION: APPENDIX F
# =============================================================================
elif selection == "Appendix F: Derivation Process & Thresholds":
    st.header("📂 Appendix F: Derivation Process and Threshold Choices")
    st.markdown("""
    This section details the **step-by-step derivation logic** used to align census populations with mortality records.
    The table includes the **metadata** (Thresholds), **Step 1** (Population Denominator Reconstruction), **Step 2** (Zero-Age Numerator Reconstruction), and **Step 3** (Final Estimation).
    """)

    file_name = "part2_appendix_f.xlsx"
    df = load_data(file_name, header_arg=[0, 1])

    if df is not None:
        csv = df.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="💾 Download Full Dataset (CSV)",
            data=csv,
            file_name="derivation_thresholds_appendix_f.csv",
            mime="text/csv"
        )

        st.divider()
        st.subheader("🔍 Explore Calculation Steps by Province")

        df_display = df.copy()
        province_col_key = None
        for col in df_display.columns:
            if "PROVINCE" in str(col).upper() or "İL" in str(col).upper():
                province_col_key = col
                break

        if province_col_key:
            provinces_list = df_display[province_col_key].unique()
            selected_province = st.selectbox("Select Province:", provinces_list)
            filtered_df = df_display[df_display[province_col_key] == selected_province]

            st.markdown(f"**Showing details for: {selected_province}**")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.warning("Could not automatically detect 'Province' column. Showing full table:")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning(f"⚠️ File '{file_name}' not found in 'data/' folder.")

# =============================================================================
# SECTION: APPENDIX G
# =============================================================================
elif selection == "Appendix G: Zero-Age Tables & Graphs":
    st.header("📂 Appendix G: Zero-Age Population Estimates")
    st.markdown(
        "This section presents the final **zero-age population estimates** derived using the Ratio-Based PDC Reconstruction Method.")

    file_name = "part2_appendix_g.xlsx"
    df = load_data(file_name)

    if df is not None:
        st.subheader("📊 Data Table")
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns([1, 5])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name="zero_age_estimates_appendix_g.csv",
                mime="text/csv"
            )

        st.divider()

        with st.expander("📈 Visualize Data (Interactive Graphs)", expanded=False):
            st.subheader("Population Trends")

            df.columns = [str(c).upper().strip() for c in df.columns]
            col_province = next((c for c in df.columns if 'LEVEL' in c or 'PROVINCE' in c), None)
            col_year = 'YEAR'
            col_value = 'TOTAL'

            if col_province and col_year in df.columns:
                provinces_list = df[col_province].unique()
                selected_province = st.selectbox("Select Level / Province:", provinces_list)

                filtered_df = df[df[col_province] == selected_province]

                y_columns = []
                if 'TOTAL' in df.columns: y_columns.append('TOTAL')
                if 'MALE' in df.columns: y_columns.append('MALE')
                if 'FEMALE' in df.columns: y_columns.append('FEMALE')

                if not y_columns and col_value in df.columns:
                    y_columns = [col_value]

                if y_columns:
                    fig = px.line(
                        filtered_df,
                        x=col_year,
                        y=y_columns,
                        markers=True,
                        title=f"Zero-Age Population Estimates: {selected_province}",
                        labels={col_year: "Year", "value": "Population", "variable": "Group"}
                    )
                    fig.update_layout(hovermode="x unified", legend_title_text="Sex")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not find columns (TOTAL, MALE, FEMALE) to plot.")
            else:
                st.error(f"Column mismatch! Needed 'YEAR' and 'LEVEL/PROVINCE'. Found: {list(df.columns)}")
    else:
        st.warning(f"⚠️ File '{file_name}' not found in 'data/' folder.")

# =============================================================================
# SECTION: APPENDIX H (YENİ EKLENEN & GÜNCELLENEN KISIM)
# =============================================================================
elif selection == "Appendix H: Demographic Convergence":
    st.header("📂 Appendix H: Demographic Convergence (Urbanization)")
    st.markdown("""
    This section provides the comprehensive dataset detailing the ratio of the **Province and District Center (PDC) Population to the Total Population** across all 81 provinces.

    As rural-to-urban migration accelerated in Türkiye, the administrative coverage of mortality statistics naturally expanded. This dataset demonstrates the progressive convergence of covered populations with true provincial populations over census years.
    """)

    # Dosya isminizi aynen bırakıyorum.
    # Not: 'asd' sayfasını Excel'de varsayılan (ilk sayfa) olarak bıraktığınızı varsayıyoruz.
    file_name = "part2_appendix_h_sehir_merkezi.xlsx"

    try:
        file_path = os.path.join("data", file_name)
        if os.path.exists(file_path):
            # Yeni formata göre header=0 (yani ilk satır başlık) olarak güncelledik.
            # Eğer uygulamanız sayfayı bulamazsa pd.read_excel(file_path, sheet_name="asd") şeklinde değiştirebilirsiniz.
            df_h = pd.read_excel(file_path, header=0)

            # Sütun isimlerini Streamlit için temizliyoruz
            df_h.rename(columns={'YEAR': 'Year', 'PROVINCE': 'Province'}, inplace=True)

            st.subheader("📊 Convergence Data Table")
            st.dataframe(df_h, use_container_width=True)

            csv = df_h.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download Demographic Convergence Data (CSV)",
                data=csv,
                file_name="demographic_convergence_appendix_h.csv",
                mime="text/csv"
            )

            st.divider()

            # ---------- GÜNCELLENEN ÇOKLU GRAFİK KISMI ----------
            with st.expander("📈 Visualize Urbanization Convergence", expanded=False):
                st.markdown(
                    "Select a province to view how its PDC population coverage increased over time by **Total, Male, and Female** populations.")

                # Yeni dosyadaki Rate sütunlarının tam isimleri:
                rate_cols = ['Rate TOTAL', 'Rate MALE', 'Rate FEMALE']

                if 'Province' in df_h.columns and 'Year' in df_h.columns and all(
                        col in df_h.columns for col in rate_cols):
                    # Null olan satırları atla
                    df_clean = df_h.dropna(subset=['Year', 'Province'] + rate_cols)

                    provinces_list = df_clean['Province'].unique()
                    selected_province = st.selectbox("Select Province:", provinces_list, key="h_prov_select")

                    filtered_df = df_clean[df_clean['Province'] == selected_province]

                    # y eksenine array olarak birden fazla sütun veriyoruz (Total, Male, Female)
                    fig = px.line(
                        filtered_df,
                        x='Year',
                        y=rate_cols,
                        markers=True,
                        title=f"Population Coverage Rate (PDC vs Total) Over Time: {selected_province}",
                        labels={'Year': "Census Year", 'value': "Coverage Ratio (0 to 1)", 'variable': "Group"}
                    )
                    # Mouse üzerine gelince hepsini göster (hovermode) ve y eksenini % formatına getir
                    fig.update_layout(yaxis_tickformat='.1%', hovermode="x unified", legend_title_text="Coverage Type")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(
                        "Required columns ('Year', 'Province', 'Rate TOTAL', 'Rate MALE', 'Rate FEMALE') not found for plotting. Please ensure the Excel file format is correct.")

        else:
            st.warning(f"⚠️ File '{file_name}' not found in 'data/' folder. Please upload it.")
    except Exception as e:
        st.error(f"Error loading Appendix H data: {e}")