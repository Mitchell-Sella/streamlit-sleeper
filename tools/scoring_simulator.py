import streamlit as st
import pandas as pd
import random
from sleeper_wrapper import Players, Stats

# Initialize Sleeper API wrappers
players = Players()
stats = Stats()

# Function to get player stats for the entire season
def get_season_stats(season):
    season_stats = {}
    for week in range(1, 19):
        week_stats = stats.get_week_stats("regular", season, week)
        for player_id, stat_line in week_stats.items():
            if player_id not in season_stats:
                season_stats[player_id] = stat_line
            else:
                for stat, value in stat_line.items():
                    season_stats[player_id][stat] = season_stats[player_id].get(stat, 0) + value
    return season_stats

# Function to calculate player scores based on custom settings
def calculate_scores(player_stats, scoring_settings):
    scores = {}
    for player_id, stat_line in player_stats.items():
        score = sum(stat_line.get(stat, 0) * value for stat, value in scoring_settings.items())
        scores[player_id] = score
    return scores

# Default scoring settings
default_scoring = {
    # Passing
    "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0, "pass_att": 0.0, "pass_cmp": 0.0, "pass_inc": 0.0, "pass_2pt": 2.0,
    # Rushing
    "rush_yd": 0.1, "rush_td": 6.0, "rush_att": 0.0, "rush_2pt": 2.0,
    # Receiving
    "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rec_target": 0.0, "rec_2pt": 2.0,
    # Kicking
    "fgm": 3.0, "fgm_0_19": 3.0, "fgm_20_29": 3.0, "fgm_30_39": 3.0, "fgm_40_49": 4.0, "fgm_50p": 5.0,
    "fgmiss": -1.0, "xpm": 1.0, "xpmiss": -1.0,
    # Team Defense
    "def_td": 6.0, "pts_allow_0": 10.0, "pts_allow_1_6": 7.0, "pts_allow_7_13": 4.0, "pts_allow_14_20": 1.0,
    "pts_allow_21_27": 0.0, "pts_allow_28_34": -1.0, "pts_allow_35p": -4.0,
    # Special Teams Defense
    "blk_kick": 2.0, "def_st_td": 6.0, "def_st_ff": 1.0, "def_st_fum_rec": 1.0,
    # Special Teams Player
    "st_td": 6.0, "st_ff": 1.0, "st_fum_rec": 1.0,
    # Misc
    "fum_lost": -2.0, "fum_rec_td": 6.0,
    # Bonus
    "bonus_rush_yd_100": 3.0, "bonus_rush_yd_200": 6.0, "bonus_rec_yd_100": 3.0, "bonus_rec_yd_200": 6.0,
    "bonus_pass_yd_300": 3.0, "bonus_pass_yd_400": 6.0,
    # IDP
    "idp_solo": 1.0, "idp_asst": 0.5, "idp_sack": 2.0, "idp_int": 3.0, "idp_fum_force": 3.0, "idp_fum_rec": 2.0,
    "idp_def_td": 6.0, "idp_pass_def": 1.0, "idp_safety": 2.0, "idp_blk_kick": 2.0
}

# Function to randomize scoring settings
def randomize_scoring():
    return {k: round(random.uniform(-5, 10), 2) for k in default_scoring.keys()}

# Streamlit app
st.title("Season-Long Scoring Simulator")

# Season selection
season = st.selectbox("Select Season", options=[2023, 2022, 2021])

# Position multi-select
positions = st.multiselect("Select Positions", options=["QB", "RB", "WR", "TE", "K", "DEF", "IDP"], default=["QB", "RB", "WR", "TE"])

# Randomize and Reset buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Randomize Scoring"):
        st.session_state.scoring = randomize_scoring()
with col2:
    if st.button("Reset to Default"):
        st.session_state.scoring = default_scoring.copy()

# Initialize session state for scoring if not exists
if 'scoring' not in st.session_state:
    st.session_state.scoring = default_scoring.copy()

# User inputs for scoring settings
st.header("Scoring Settings")

# Create tabs for different categories
tabs = st.tabs(["Passing", "Rushing", "Receiving", "Kicking", "Team Defense", "Special Teams", "Misc", "Bonus", "IDP"])

with tabs[0]:
    st.subheader("Passing")
    st.session_state.scoring["pass_yd"] = st.number_input("Points per Passing Yard", value=st.session_state.scoring["pass_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["pass_td"] = st.number_input("Points per Passing TD", value=st.session_state.scoring["pass_td"], step=0.5)
    st.session_state.scoring["pass_int"] = st.number_input("Points per Interception", value=st.session_state.scoring["pass_int"], step=0.5)
    st.session_state.scoring["pass_att"] = st.number_input("Points per Pass Attempt", value=st.session_state.scoring["pass_att"], step=0.1)
    st.session_state.scoring["pass_cmp"] = st.number_input("Points per Pass Completion", value=st.session_state.scoring["pass_cmp"], step=0.1)
    st.session_state.scoring["pass_inc"] = st.number_input("Points per Incomplete Pass", value=st.session_state.scoring["pass_inc"], step=0.1)
    st.session_state.scoring["pass_2pt"] = st.number_input("Points per 2PT Conversion", value=st.session_state.scoring["pass_2pt"], step=0.5)

with tabs[1]:
    st.subheader("Rushing")
    st.session_state.scoring["rush_yd"] = st.number_input("Points per Rushing Yard", value=st.session_state.scoring["rush_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["rush_td"] = st.number_input("Points per Rushing TD", value=st.session_state.scoring["rush_td"], step=0.5)
    st.session_state.scoring["rush_att"] = st.number_input("Points per Rush Attempt", value=st.session_state.scoring["rush_att"], step=0.1)
    st.session_state.scoring["rush_2pt"] = st.number_input("Points per 2PT Conversion (Rush)", value=st.session_state.scoring["rush_2pt"], step=0.5)

with tabs[2]:
    st.subheader("Receiving")
    st.session_state.scoring["rec"] = st.number_input("Points per Reception", value=st.session_state.scoring["rec"], step=0.5)
    st.session_state.scoring["rec_yd"] = st.number_input("Points per Receiving Yard", value=st.session_state.scoring["rec_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["rec_td"] = st.number_input("Points per Receiving TD", value=st.session_state.scoring["rec_td"], step=0.5)
    st.session_state.scoring["rec_target"] = st.number_input("Points per Target", value=st.session_state.scoring["rec_target"], step=0.1)
    st.session_state.scoring["rec_2pt"] = st.number_input("Points per 2PT Conversion (Receiving)", value=st.session_state.scoring["rec_2pt"], step=0.5)

with tabs[3]:
    st.subheader("Kicking")
    st.session_state.scoring["fgm"] = st.number_input("Points per Field Goal Made", value=st.session_state.scoring["fgm"], step=0.5)
    st.session_state.scoring["fgm_0_19"] = st.number_input("Points per FG Made (0-19 yards)", value=st.session_state.scoring["fgm_0_19"], step=0.5)
    st.session_state.scoring["fgm_20_29"] = st.number_input("Points per FG Made (20-29 yards)", value=st.session_state.scoring["fgm_20_29"], step=0.5)
    st.session_state.scoring["fgm_30_39"] = st.number_input("Points per FG Made (30-39 yards)", value=st.session_state.scoring["fgm_30_39"], step=0.5)
    st.session_state.scoring["fgm_40_49"] = st.number_input("Points per FG Made (40-49 yards)", value=st.session_state.scoring["fgm_40_49"], step=0.5)
    st.session_state.scoring["fgm_50p"] = st.number_input("Points per FG Made (50+ yards)", value=st.session_state.scoring["fgm_50p"], step=0.5)
    st.session_state.scoring["fgmiss"] = st.number_input("Points per Missed FG", value=st.session_state.scoring["fgmiss"], step=0.5)
    st.session_state.scoring["xpm"] = st.number_input("Points per Extra Point Made", value=st.session_state.scoring["xpm"], step=0.5)
    st.session_state.scoring["xpmiss"] = st.number_input("Points per Missed Extra Point", value=st.session_state.scoring["xpmiss"], step=0.5)

with tabs[4]:
    st.subheader("Team Defense")
    st.session_state.scoring["def_td"] = st.number_input("Points per Defensive TD", value=st.session_state.scoring["def_td"], step=0.5)
    st.session_state.scoring["pts_allow_0"] = st.number_input("Points for 0 Points Allowed", value=st.session_state.scoring["pts_allow_0"], step=0.5)
    st.session_state.scoring["pts_allow_1_6"] = st.number_input("Points for 1-6 Points Allowed", value=st.session_state.scoring["pts_allow_1_6"], step=0.5)
    st.session_state.scoring["pts_allow_7_13"] = st.number_input("Points for 7-13 Points Allowed", value=st.session_state.scoring["pts_allow_7_13"], step=0.5)
    st.session_state.scoring["pts_allow_14_20"] = st.number_input("Points for 14-20 Points Allowed", value=st.session_state.scoring["pts_allow_14_20"], step=0.5)
    st.session_state.scoring["pts_allow_21_27"] = st.number_input("Points for 21-27 Points Allowed", value=st.session_state.scoring["pts_allow_21_27"], step=0.5)
    st.session_state.scoring["pts_allow_28_34"] = st.number_input("Points for 28-34 Points Allowed", value=st.session_state.scoring["pts_allow_28_34"], step=0.5)
    st.session_state.scoring["pts_allow_35p"] = st.number_input("Points for 35+ Points Allowed", value=st.session_state.scoring["pts_allow_35p"], step=0.5)

with tabs[5]:
    st.subheader("Special Teams")
    st.session_state.scoring["blk_kick"] = st.number_input("Points per Blocked Kick", value=st.session_state.scoring["blk_kick"], step=0.5)
    st.session_state.scoring["def_st_td"] = st.number_input("Points per Special Teams TD", value=st.session_state.scoring["def_st_td"], step=0.5)
    st.session_state.scoring["def_st_ff"] = st.number_input("Points per Special Teams Forced Fumble", value=st.session_state.scoring["def_st_ff"], step=0.5)
    st.session_state.scoring["def_st_fum_rec"] = st.number_input("Points per Special Teams Fumble Recovery", value=st.session_state.scoring["def_st_fum_rec"], step=0.5)
    st.session_state.scoring["st_td"] = st.number_input("Points per Special Teams Player TD", value=st.session_state.scoring["st_td"], step=0.5)
    st.session_state.scoring["st_ff"] = st.number_input("Points per Special Teams Player Forced Fumble", value=st.session_state.scoring["st_ff"], step=0.5)
    st.session_state.scoring["st_fum_rec"] = st.number_input("Points per Special Teams Player Fumble Recovery", value=st.session_state.scoring["st_fum_rec"], step=0.5)

with tabs[6]:
    st.subheader("Misc")
    st.session_state.scoring["fum_lost"] = st.number_input("Points per Fumble Lost", value=st.session_state.scoring["fum_lost"], step=0.5)
    st.session_state.scoring["fum_rec_td"] = st.number_input("Points per Fumble Recovery TD", value=st.session_state.scoring["fum_rec_td"], step=0.5)

with tabs[7]:
    st.subheader("Bonus")
    st.session_state.scoring["bonus_rush_yd_100"] = st.number_input("Bonus Points for 100-199 Rushing Yards", value=st.session_state.scoring["bonus_rush_yd_100"], step=0.5)
    st.session_state.scoring["bonus_rush_yd_200"] = st.number_input("Bonus Points for 200+ Rushing Yards", value=st.session_state.scoring["bonus_rush_yd_200"], step=0.5)
    st.session_state.scoring["bonus_rec_yd_100"] = st.number_input("Bonus Points for 100-199 Receiving Yards", value=st.session_state.scoring["bonus_rec_yd_100"], step=0.5)
    st.session_state.scoring["bonus_rec_yd_200"] = st.number_input("Bonus Points for 200+ Receiving Yards", value=st.session_state.scoring["bonus_rec_yd_200"], step=0.5)
    st.session_state.scoring["bonus_pass_yd_300"] = st.number_input("Bonus Points for 300-399 Passing Yards", value=st.session_state.scoring["bonus_pass_yd_300"], step=0.5)
    st.session_state.scoring["bonus_pass_yd_400"] = st.number_input("Bonus Points for 400+ Passing Yards", value=st.session_state.scoring["bonus_pass_yd_400"], step=0.5)

with tabs[8]:
    st.subheader("IDP (Individual Defensive Players)")
    st.session_state.scoring["idp_solo"] = st.number_input("Points per Solo Tackle", value=st.session_state.scoring["idp_solo"], step=0.5)
    st.session_state.scoring["idp_asst"] = st.number_input("Points per Assisted Tackle", value=st.session_state.scoring["idp_asst"], step=0.5)
    st.session_state.scoring["idp_sack"] = st.number_input("Points per Sack", value=st.session_state.scoring["idp_sack"], step=0.5)
    st.session_state.scoring["idp_int"] = st.number_input("Points per Interception", value=st.session_state.scoring["idp_int"], step=0.5)
    st.session_state.scoring["idp_fum_force"] = st.number_input("Points per Forced Fumble", value=st.session_state.scoring["idp_fum_force"], step=0.5)
    st.session_state.scoring["idp_fum_rec"] = st.number_input("Points per Fumble Recovery", value=st.session_state.scoring["idp_fum_rec"], step=0.5)
    st.session_state.scoring["idp_def_td"] = st.number_input("Points per Defensive TD", value=st.session_state.scoring["idp_def_td"], step=0.5)
    st.session_state.scoring["idp_pass_def"] = st.number_input("Points per Pass Defended", value=st.session_state.scoring["idp_pass_def"], step=0.5)
    st.session_state.scoring["idp_safety"] = st.number_input("Points per Safety", value=st.session_state.scoring["idp_safety"], step=0.5)
    st.session_state.scoring["idp_blk_kick"] = st.number_input("Points per Blocked Kick", value=st.session_state.scoring["idp_blk_kick"], step=0.5)

if st.button("Calculate Season Scores"):
    with st.spinner("Fetching and calculating season stats..."):
        # Get player stats for the entire season
        player_stats = get_season_stats(season)

        if player_stats:
            # Calculate scores based on custom settings
            scores = calculate_scores(player_stats, st.session_state.scoring)

            # Get player details
            all_players = players.get_all_players()

            # Create a dataframe with player details and scores
            data = []
            for player_id, score in scores.items():
                if player_id in all_players:
                    player = all_players[player_id]
                    if player['position'] in positions:
                        data.append({
                            "Player": f"{player['first_name']} {player['last_name']}",
                            "Position": player['position'],
                            "Team": player['team'],
                            "Total Score": round(score, 2)
                        })

            df = pd.DataFrame(data)
            df = df.sort_values("Total Score", ascending=False).reset_index(drop=True)

            # Display top players
            st.header(f"Top Players for {season} Season")
            st.dataframe(df.head(50))

            # Optional: Add a download button for the full results
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Full Results",
                data=csv,
                file_name=f"fantasy_scores_{season}.csv",
                mime="text/csv",
            )

        else:
            st.error("Failed to retrieve player stats. Please try again.")