import streamlit as st
import requests


def get_user_id(username):
    base_url = 'https://api.sleeper.app'
    endpoint = f'/v1/user/{username}'
    response = requests.get(base_url + endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def run():
    """
    Main function for Hello World.
    """
    st.set_page_config(
        page_title="Home",
        page_icon="https://sleeper.com/favicon.ico",
    )


if __name__ == "__main__":
    run()
