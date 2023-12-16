import streamlit as st
import requests

@st.cache_data
def get_players():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )

    get_players()


if __name__ == "__main__":
    run()
