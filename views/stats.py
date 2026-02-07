import streamlit as st

def show(analyzer):
    st.header("League Summary")

    # 1. General Stats
    stats = analyzer.calculate_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", stats.get('total_trades', 0))

    with col2:
        most_active = stats.get('most_active_trader')
        if most_active:
            st.metric("Most Active",
                      f"{most_active['name']}",
                      f"{most_active['count']} trades")
        else:
            st.metric("Most Active", "N/A")

    with col3:
        least_active = stats.get('least_active_trader')
        if least_active:
            st.metric("Least Active",
                      f"{least_active['name']}",
                      f"{least_active['count']} trades")
        else:
            st.metric("Least Active", "N/A")

    with col4:
        days = stats.get('days_since_last_trade')
        if days is not None:
            st.metric("Days Since Trade", f"{days}")
        else:
            st.metric("Days Since Trade", "N/A")

    st.divider()

    # 2. Trade Matrix
    st.subheader("Trade Matrix")
    st.caption("Number of trades between each pair of teams.")

    matrix = analyzer.get_trade_matrix()

    if not matrix.empty:
        # Display with heatmap style
        st.dataframe(
            matrix.style.background_gradient(cmap='Blues', axis=None),
            use_container_width=True
        )
    else:
        st.info("No trades found to generate matrix.")
