import streamlit as st
import pandas as pd

def show(analyzer):
    st.header("League Summary")

    # 1. General Stats
    stats = analyzer.calculate_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Trades", stats.get('total_trades', 0))
        st.caption("*Note: Total Trades may not match the matrix sum due to multi-team trades.*")

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

    st.divider()

    # 2. Trade Matrix
    st.subheader("Trade Matrix")

    matrix = analyzer.get_trade_matrix()

    if not matrix.empty:
        # Store original matrix for vmax calculation to avoid skewing colors
        original_matrix = matrix.copy()
        vmax = original_matrix.max().max() if not original_matrix.empty else 1

        # Calculate Totals
        # Row Sum = Total Sent (Proposals)
        matrix['Total Sent'] = matrix.sum(axis=1)

        # Col Sum = Total Received (Accepted)
        # Note: sum() includes the new 'Total Sent' column, so we must exclude it or compute before
        # Easier: Compute col sums on original data, then append
        col_sums = matrix.drop(columns=['Total Sent']).sum(axis=0)

        # Add Total Received Row
        matrix.loc['Total Received'] = col_sums

        # Calculate Grand Total (bottom right corner)
        # It is the sum of 'Total Sent' column (which is now in the matrix)
        # OR sum of col_sums
        grand_total = col_sums.sum()
        matrix.loc['Total Received', 'Total Sent'] = grand_total

        # Convert floats to ints (pandas sum might produce floats if any NaN, but we initialized with 0)
        matrix = matrix.fillna(0).astype(int)

        st.info("Rows represent the **Proposer** (Sender). Columns represent the **Accepter** (Receiver).")

        # Rename axes for clarity
        matrix.index.name = "Sender (Proposer)"
        matrix.columns.name = "Accepter"

        # Display with heatmap style
        # We use vmax based on individual trades so totals (which are large) don't skew the gradient
        # Removing subset to ensure totals are visible (they will be dark blue, but visible)
        st.dataframe(
            matrix.style.background_gradient(cmap='Blues', axis=None, vmax=vmax),
            use_container_width=True
        )

        with st.expander("Debug Matrix Data"):
            st.write("Matrix Shape:", matrix.shape)
            st.write("Index:", matrix.index.tolist())
            st.write("Columns:", matrix.columns.tolist())
            st.dataframe(matrix) # Raw data
    else:
        st.info("No trades found to generate matrix.")
