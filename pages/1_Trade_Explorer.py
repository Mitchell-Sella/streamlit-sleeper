import streamlit as st
from views import stats as stats_view

st.set_page_config(page_title="Trade Explorer", page_icon=":material/swap_horiz:", layout="wide")

if 'analyzer' in st.session_state and st.session_state.analyzer:
    stats_view.show(st.session_state.analyzer)
else:
    st.info("Please load league data on the Home page first.")
