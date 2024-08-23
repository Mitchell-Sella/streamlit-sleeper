import streamlit as st

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

# import streamlit as st
# import pandas as pd
# from sleeper_wrapper import Drafts
# from utils import init_session_state, load_players
# import json
#
# # Initialize session state
# init_session_state()
#
# # Page title
# st.title("Rankings Builder")
#
#
# # Function to get draft data
# def get_draft_data(draft_id):
#     draft = Drafts(draft_id)
#     picks = draft.get_all_picks()
#
#     extracted_data = []
#     for item in picks:
#         player_data = {
#             'player_id': item['player_id'],
#             'full_name': f"{item['metadata']['first_name']} {item['metadata']['last_name']}",
#             'position': item['metadata']['position'],
#             'team_abbr': item['metadata']['team'],
#             'rank': item['pick_no'],
#             'tier': '',  # Empty tier column
#             'salary_cap': ''  # Empty salary_cap column
#         }
#         extracted_data.append(player_data)
#
#     return pd.DataFrame(extracted_data)
#
#
# # Default rankings import
# st.write("### Use Rankings From Completed Draft")
# draft_id = st.text_input(
#     label="Enter Draft ID",
#     value=st.session_state.perm.get('draft_id', ''),
#     key="temp_draft_id"
# )
#
# if st.button("Load Draft"):
#     if draft_id:
#         try:
#             df = get_draft_data(draft_id)
#             st.session_state.perm['rankings'] = df
#             st.session_state.perm['draft_id'] = draft_id
#             st.success(f"Draft {draft_id} loaded successfully!")
#         except Exception as e:
#             st.error(f"Error loading draft: {str(e)}")
#     else:
#         st.warning("Please enter a valid Draft ID")
#
# # Rest of your code for file upload and data editing...
#
# # Data upload helpful text
# st.write("### Upload Your Rankings")
# st.markdown("Upload a CSV file with your rankings. The file should have the following columns:")
#
# st.markdown("""
# - ``player_id``: Unique identifier for the player
# - ``full_name``: Player's first and last name
# - ``position``: Player's position (e.g., QB, RB, WR, TE)
# - ``team_abbr``: Player's team abbreviation
# - ``rank``: Player's rank in your list
# - ``tier``: Tier grouping for the player
# - ``salary_cap``: Salary cap value for the player
# """)
#
# # File upload option
# uploaded_file = st.file_uploader(label="Upload rankings CSV", type="csv")
# if uploaded_file is not None:
#     try:
#         df = pd.read_csv(uploaded_file)
#         st.session_state.perm['rankings'] = df
#         st.success("Rankings uploaded successfully!")
#     except Exception as e:
#         st.error(f"Error reading the file: {str(e)}")
#
# # Data editor helpful text
# st.write("### Edit Rankings")
# st.markdown("You can edit the rankings directly in the table below. Click on any cell to modify its value.")
# st.markdown("- To add a new row, click the ➕ button at the bottom of the table.")
# st.markdown("- To delete a row, select it and click the 🗑️ button at the top of the table.")
#
# # Load players data (assuming you have a function to do this)
# players = load_players()
#
#
# # Function to get player details
# def get_player_details(full_name):
#     player = players[players['full_name'] == full_name].iloc[0]
#     return {
#         'player_id': player['player_id'],
#         'position': player['position'],
#         'team_abbr': player['team_abbr']
#     }
#
#
# # Create a dictionary for easy lookup
# player_details = {name: get_player_details(name) for name in players['full_name']}
#
#
# # Function to update other fields when full_name is selected
# def update_player_fields(index, field, value):
#     if field == 'full_name' and value in player_details:
#         details = player_details[value]
#         for key, val in details.items():
#             st.session_state.perm['rankings'].at[index, key] = val
#
#
# # Configure the data editor
# if 'rankings' in st.session_state.perm:
#     edited_df = st.data_editor(
#         st.session_state.perm['rankings'],
#         num_rows="dynamic",
#         column_config={
#             "full_name": st.column_config.SelectboxColumn(
#                 "Full Name",
#                 options=players['full_name'].tolist(),
#                 required=True
#             ),
#             "player_id": st.column_config.NumberColumn(
#                 "Player ID",
#                 disabled=True
#             ),
#             "position": st.column_config.TextColumn(
#                 "Position",
#                 disabled=True
#             ),
#             "team_abbr": st.column_config.TextColumn(
#                 "Team",
#                 disabled=True
#             ),
#             "rank": st.column_config.NumberColumn(
#                 "Rank",
#                 required=True
#             ),
#             "tier": st.column_config.NumberColumn(
#                 "Tier",
#                 required=False
#             ),
#             "salary_cap": st.column_config.NumberColumn(
#                 "Salary Cap",
#                 required=False
#             )
#         },
#         on_change=update_player_fields,
#         key="rankings_editor"
#     )
#
#     # Update session state with edited DataFrame
#     st.session_state.perm['rankings'] = edited_df
#
#     # Data download helpful text
#     st.write("### Save Your Rankings")
#     st.markdown("Click the button below to download your current rankings as a CSV file. "
#                 "You can upload this file to use your custom rankings in the Draft Assistant.")
#
#     # Download option
#     csv = edited_df.to_csv(index=False)
#     st.download_button(
#         label="Download rankings",
#         data=csv,
#         file_name="rankings.csv",
#         mime="text/csv"
#     )
# else:
#     st.info("Please load a draft or upload rankings to edit.")