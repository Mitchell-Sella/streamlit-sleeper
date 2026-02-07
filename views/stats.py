import streamlit as st
import pandas as pd

def show(analyzer):
    st.header("League Stats")

    stats = analyzer.calculate_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Trades", stats.get('total_trades', 0))

    with col2:
        most_active = stats.get('most_active_trader')
        if most_active:
            st.metric("Most Active Trader",
                      f"{most_active['name']}",
                      f"{most_active['count']} trades")
        else:
            st.metric("Most Active Trader", "N/A")

    with col3:
        # Placeholder
        st.metric("Avg Trades/Week", f"{stats.get('total_trades', 0) / 18:.1f}" if stats.get('total_trades') else "0")
