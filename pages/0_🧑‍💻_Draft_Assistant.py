import streamlit as st
from sleeper_wrapper import User, League, Drafts
from utils import check_user

st.title("Draft Assistant")

check_user()

league = League(st.session_state.league_id)
drafts = league.get_all_drafts()
st.write(drafts)
draft_ids = [draft['draft_id'] for draft in drafts]

draft_id = st.selectbox("Select League", options=draft_ids)

draft = Drafts(draft_id)
draft_picks = draft.get_all_picks()
st.write(draft_picks)
user_id = st.session_state.user.get_user_id()

user_picks = [pick for pick in draft_picks if pick['picked_by'] == user_id]