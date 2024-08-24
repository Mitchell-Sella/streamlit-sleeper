import streamlit as st
import pandas as pd
from sleeper_wrapper import User, League, Drafts
from utils import load_players

# Page title
st.title("Draft Assistant")

if st.session_state.perm['user_name'] == "" or st.session_state.perm['league_name'] == "":
    st.warning("Please select a username and league on the sidebar.")
else:
    user = User(st.session_state.perm['user_name'])
    drafts = user.get_all_drafts(sport="nfl", season=2024)

    # Create a list of options for the dropdown
    options = [
        f"{format_timestamp(draft['start_time'])} - {draft['status']} (ID: {draft['draft_id']})"
        for draft in drafts if draft['league_id'] == st.session_state.perm['league_id']
    ]

    # Create the dropdown
    selected_option = st.selectbox("Select a draft:", options)

    # Extract the draft_id from the selected option
    if selected_option:
        selected_draft_id = selected_option.split("(ID: ")[-1].rstrip(")")

        # Find the selected draft in the original data
        selected_draft = next((draft for draft in drafts if draft['draft_id'] == selected_draft_id), None)
        if selected_draft:
            draft = Drafts(selected_draft_id)
            picks = draft.get_all_picks()
            user_picks = [
                [f"{pick['round']}.{pick['draft_slot']:02}", f"{pick['metadata']['first_name']} {pick['metadata']['last_name']}"]
                for pick in picks if pick['picked_by'] == user.get_user_id()]
            st.write("Draft picks:")
            st.table(user_picks)


def format_timestamp(timestamp):
    """
    Format timestamp to string.
    """
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
