import streamlit as st
from views import stats as stats_view

# Page config is handled in entrypoint now
# st.set_page_config(...)

if 'analyzer' in st.session_state and st.session_state.analyzer:
    stats_view.show(st.session_state.analyzer)
else:
    st.info("Please load league data on the Home page first.")
