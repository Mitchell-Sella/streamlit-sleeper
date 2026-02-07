import streamlit as st
import pandas as pd
from services.sleeper import SleeperService

def show(analyzer):
    st.header("Player Path Explorer")
    st.markdown("Trace a player's journey through the league via trades and waivers.")

    # Fetch all players (cached)
    with st.spinner("Loading player database..."):
        try:
            all_players = SleeperService.get_all_players()
        except Exception as e:
            st.error(f"Failed to load players: {e}")
            return

    # Get all player IDs involved in transactions
    involved_players = set()
    for txn in analyzer.transactions:
        if txn.get('adds'):
            involved_players.update(txn['adds'].keys())
        if txn.get('drops'):
            involved_players.update(txn['drops'].keys())

    # Filter all_players to only include those involved in transactions
    # Note: Using dict comprehension
    active_players = {pid: all_players.get(pid, {'first_name': 'Unknown', 'last_name': 'Player', 'position': '?'})
                      for pid in involved_players if pid in all_players}

    if not active_players:
        st.warning("No player movements found in this league/season.")
        return

    # Create options: "Name (Position - Team)"
    player_options = {}
    for pid, p in active_players.items():
        first = p.get('first_name', 'Unknown')
        last = p.get('last_name', 'Player')
        pos = p.get('position', '?')
        team = p.get('team', 'FA') or 'FA'
        label = f"{first} {last} ({pos} - {team})"
        player_options[label] = pid

    selected_player_label = st.selectbox("Search for a Player", options=sorted(player_options.keys()))

    if selected_player_label:
        player_id = player_options[selected_player_label]
        path = analyzer.get_player_path(player_id)

        st.subheader(f"History: {selected_player_label}")

        if not path:
            st.info("No movements recorded for this player.")
        else:
            # Display as a table
            df = pd.DataFrame(path)
            # Format date
            df['date'] = pd.to_datetime(df['date'], unit='ms').dt.strftime('%Y-%m-%d')

            # Styling the table
            st.dataframe(df[['date', 'type', 'from', 'to']], use_container_width=True)

            # Graphviz Visualization
            try:
                dot = "digraph {\n"
                dot += "  rankdir=LR;\n"
                dot += "  node [style=filled, fillcolor=lightblue];\n"

                # Collect all unique teams to declare nodes
                teams = set()
                for event in path:
                    teams.add(event['from'])
                    teams.add(event['to'])

                # Define nodes
                for team in teams:
                    # Escape quotes in team names
                    safe_team = team.replace('"', '\\"')
                    dot += f'  "{safe_team}" [shape=box];\n'

                # Define edges
                for event in path:
                    safe_from = event['from'].replace('"', '\\"')
                    safe_to = event['to'].replace('"', '\\"')
                    label = f"{event['type']}\\n{event['date']}"
                    dot += f'  "{safe_from}" -> "{safe_to}" [label="{label}", fontsize=10];\n'

                dot += "}"
                st.graphviz_chart(dot)
            except Exception as e:
                st.error(f"Could not render graph: {e}")
