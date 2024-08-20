import streamlit as st
from sleeper_wrapper import User, League, Drafts
from utils import format_timestamp, init_session_state

st.title("Draft Assistant")

init_session_state()

user = User(st.session_state.persistent_data['user_name'])
drafts = user.get_all_drafts(sport="nfl", season=2024)

# Create a list of options for the dropdown
options = [
    f"{format_timestamp(draft['start_time'])} - {draft['status']} (ID: {draft['draft_id']})"
    for draft in drafts if draft['league_id'] == st.session_state.persistent_data['league_id']
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