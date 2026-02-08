import streamlit as st

# Entrypoint for the application
# Using st.Page and st.navigation

# Define Pages
home_page = st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True)
trade_page = st.Page("app_pages/trade_explorer.py", title="Trade Explorer", icon=":material/swap_horiz:")
draft_page = st.Page("app_pages/draft_history.py", title="Draft History", icon=":material/grid_on:")

# Setup Navigation
pg = st.navigation({
    "League": [home_page],
    "Analysis": [trade_page, draft_page]
})

st.set_page_config(
    page_title="Sleeper Analytics",
    page_icon=":material/analytics:",
    layout="wide"
)

# Run Navigation
pg.run()
