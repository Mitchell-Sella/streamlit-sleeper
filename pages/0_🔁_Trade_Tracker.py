import streamlit as st

# Set page config
st.set_page_config(
    page_title="Trade Tracker",
    page_icon="https://sleeper.com/favicon.ico",
)

# Add custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:50px !important;
        font-weight: bold;
        color: #FF9633;
        text-align: center;
    }
    .medium-font {
        font-size:30px !important;
        color: #808080;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Display the under construction message
st.markdown('<p class="big-font">🚧 Under Construction 🚧</p>', unsafe_allow_html=True)
st.markdown('<p class="medium-font">We\'re working hard to bring you something amazing!</p>', unsafe_allow_html=True)

# Add additional information
st.info("Check back soon for updates!")