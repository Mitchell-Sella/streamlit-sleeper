from datetime import datetime
import streamlit as st


def init_session_state():
    """
    Initialize the session state.
    """
    if "persistent_data" not in st.session_state:
        st.session_state.persistent_data = {
            "user_name": "",
            "league_name": ""
        }


def format_timestamp(timestamp):
    """
    Format timestamp to string.
    """
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')