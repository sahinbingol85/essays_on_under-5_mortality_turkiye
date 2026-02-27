import streamlit as st

st.set_page_config(
    page_title="PhD Dissertation Digital Appendix",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 PhD Dissertation")
st.subheader("ESSAYS ON THE AGE PATTERNS OF UNDER-5 MORTALITY IN TÜRKİYE")
st.subheader("Analyzing the Present, Harmonizing the Historical Data, Unraveling the Past")

st.markdown(
    """
    **Author:** Şahin Bingöl  
    **Institute:** Hacettepe University Institute of Population Studies  
    **Year:** 2026

    ---
    ### 👋 Welcome
    This digital appendix serves as a supplementary platform for the PhD dissertation. 
    It consolidates extensive demographic data analysis into interactive visualizations.

    ### 📚 How to Navigate
    Please use the **sidebar on the left** to explore the specific parts of the thesis:

    * **📍 Recent Trends (2009-2024):** Provincial analysis of current mortality levels and patterns.
    * **👶 Harmonizing the Historical Data:** Specific focus on childhood mortality determinants.
    * **⏳ Historical Analysis:** Reconstruction of historical mortality trends (national : 1950-2008 , provincial 1931-2008).

    ---
    *Select a module from the sidebar to begin exploration.*
    """
)

st.info("👈 Please select a section from the sidebar to view the analysis.")