import streamlit as st
import requests
import sleeper_wrapper


def run():
    """
    Main function for Hello World.
    """
    st.set_page_config(
        page_title="Home",
        page_icon="https://sleeper.com/favicon.ico",
    )

    user = sleeper_wrapper.User("TheEvilNarwhal")
    leagues = user.get_all_leagues(sport="nfl", season="2023")
    print(leagues)


if __name__ == "__main__":
    run()
