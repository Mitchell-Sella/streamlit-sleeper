import streamlit as st
import pandas as pd
from services.sleeper import SleeperService
import networkx as nx

def show(analyzer):
    st.header("Trade Log & Tree Visualization")

    # --- Trade Log ---
    st.subheader("All Trades")

    # Filter by User
    users = sorted(analyzer.user_name_map.values())
    selected_users = st.multiselect("Filter by User(s)", options=users)

    # Filter transactions
    trades = [t for t in analyzer.transactions if t['type'] == 'trade']

    if selected_users:
        filtered_trades = []
        for t in trades:
            involved_names = [analyzer.roster_name_map.get(rid) for rid in t['roster_ids']]
            if any(name in selected_users for name in involved_names):
                filtered_trades.append(t)
        trades = filtered_trades

    if not trades:
        st.info("No trades found.")
    else:
        # Build DataFrame for display
        data = []
        for t in trades:
            # Format adds/drops for readability
            adds_str = ""
            # Handle case where 'adds' is None
            adds = t.get('adds') or {}
            for pid, rid in adds.items():
                owner = analyzer.roster_name_map.get(rid, f"Roster {rid}")
                p_name = analyzer.get_player_name(pid)
                adds_str += f"{owner} gets {p_name}; "

            row = {
                'Date': pd.to_datetime(t['created'], unit='ms').strftime('%Y-%m-%d'),
                'Teams': ", ".join([analyzer.roster_name_map.get(rid, str(rid)) for rid in t['roster_ids']]),
                'Details': adds_str,
                'Transaction ID': t['transaction_id'],
                'created_ts': t['created']
            }
            data.append(row)

        df = pd.DataFrame(data).sort_values('Date', ascending=False)

        # Display Table
        st.dataframe(df[['Date', 'Teams', 'Details']], use_container_width=True)

    # --- Trade Tree Visualization ---
    st.divider()
    st.subheader("Trade Tree Explorer")
    st.caption("Select a trade from below to visualize the full history and future of the involved assets.")

    # Sort trades for dropdown (newest first)
    all_trades = sorted([t for t in analyzer.transactions if t['type'] == 'trade'],
                        key=lambda x: x['created'], reverse=True)

    # Create selection options: "Date - Teams (ID)"
    trade_options = {}
    trade_labels = []
    for t in all_trades:
        date_str = pd.to_datetime(t['created'], unit='ms').strftime('%Y-%m-%d')
        teams_str = ", ".join([analyzer.roster_name_map.get(rid, str(rid)) for rid in t['roster_ids']])
        label = f"{date_str}: {teams_str} ({t['transaction_id']})"
        trade_options[label] = t['transaction_id']
        trade_labels.append(label)

    selected_label = st.selectbox("Select Trade", options=trade_labels)

    if selected_label:
        root_tid = trade_options[selected_label]

        st.markdown(f"**Tracing assets history and future...**")

        G = analyzer.build_trade_tree(root_tid)

        if G is None:
                st.error("Error building tree.")
        elif len(G.nodes) > 0:
            # Convert to Graphviz DOT format
            dot = "digraph {\n"
            dot += "  rankdir=TB;\n" # Top to Bottom flow
            dot += "  node [shape=box, style=filled, fillcolor=lightblue, fontname=\"Helvetica\"];\n"
            dot += "  edge [fontname=\"Helvetica\", fontsize=10];\n"

            # Sort nodes by date for better layout hints?
            # Graphviz handles layout automatically, but rankdir=TB helps.

            # Add nodes
            for node_id in G.nodes:
                data = analyzer.txn_map.get(node_id, {})
                date_str = pd.to_datetime(data.get('created', 0), unit='ms').strftime('%Y-%m-%d')

                # Label: Date \n Type \n Teams involved
                txn_type = data.get('type', 'Transaction').title()
                involved = [analyzer.roster_name_map.get(rid, str(rid)) for rid in data.get('roster_ids', [])]
                involved_str = "\\n".join(involved)

                label = f"{date_str}\\n{txn_type}\\n{involved_str}"

                # Highlight Root node
                color = "lightblue"
                if node_id == root_tid:
                    color = "gold"
                    label = f"SELECTED TRADE\\n{label}"
                elif txn_type == "Waiver" or txn_type == "Free_Agent":
                    color = "lightgrey"

                dot += f'  "{node_id}" [label="{label}", fillcolor={color}];\n'

            # Add edges
            for u, v in G.edges:
                label = G[u][v].get('label', '')
                safe_label = label.replace('"', '\\"')
                dot += f'  "{u}" -> "{v}" [label="{safe_label}"];\n'

            dot += "}"
            st.graphviz_chart(dot)
        else:
            st.info("No asset history found.")
