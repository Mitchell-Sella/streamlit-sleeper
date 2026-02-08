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
        # Row Sum = Total Proposed (Proposals)
        matrix['Total Proposed'] = matrix.sum(axis=1)

        # Col Sum = Total Accepted (Accepted)
        # Note: sum() includes the new 'Total Proposed' column, so we must exclude it or compute before
        # Easier: Compute col sums on original data, then append
        col_sums = matrix.drop(columns=['Total Proposed']).sum(axis=0)

        # Add Total Accepted Row
        matrix.loc['Total Accepted'] = col_sums

        # Calculate Grand Total (bottom right corner)
        grand_total = col_sums.sum()
        matrix.loc['Total Accepted', 'Total Proposed'] = grand_total

        # Convert floats to ints
        matrix = matrix.fillna(0).astype(int)

        st.info("Rows represent the **Proposer**. Columns represent the **Accepter**.")

        # Rename axes for clarity
        matrix.index.name = "Proposer"
        matrix.columns.name = "Accepter"

        # Display with heatmap style
        st.caption("Select a row (Proposer) or column (Accepter) to view details.")
        event = st.dataframe(
            matrix.style.background_gradient(cmap='Blues', axis=None, vmax=vmax),
            use_container_width=True,
            on_select="rerun",
            selection_mode=["single-row", "single-column"]
        )

        # Handle selection
        if event and (event.selection.rows or event.selection.columns):
            # Get selected row index and column name
            proposer = None
            accepter = None

            if event.selection.rows:
                row_idx = event.selection.rows[0]
                row_name = matrix.index[row_idx]
                proposer = row_name if row_name != "Total Accepted" else None

            if event.selection.columns:
                col_name = event.selection.columns[0]
                accepter = col_name if col_name != "Total Proposed" else None

            st.divider()
            st.subheader("Selected Trades")

            # Display context
            p_display = proposer if proposer else "Any"
            a_display = accepter if accepter else "Any"
            st.write(f"Showing trades: **{p_display}** (Proposer) → **{a_display}** (Accepter)")

            trades = analyzer.get_trades_between(proposer, accepter)

            if trades:
                enriched_trades = analyzer.get_enriched_trades(trades, proposer, accepter)

                for trade in enriched_trades:
                    # Format date
                    ts = trade['date'] / 1000
                    date_str = pd.to_datetime(ts, unit='s').strftime('%B %d, %Y')

                    with st.container():
                        st.markdown(f"**{date_str}**")

                        t_col1, t_col2 = st.columns(2)

                        # Left Column: Proposer
                        with t_col1:
                            st.markdown(f"#### {trade['proposer']}")
                            st.caption("Receives:")
                            if trade['proposer_receives']:
                                for asset in trade['proposer_receives']:
                                    st.markdown(f"- {asset}")
                            else:
                                st.markdown("*(Nothing)*")

                        # Right Column: Accepter
                        with t_col2:
                            st.markdown(f"#### {trade['accepter']}")
                            st.caption("Receives:")
                            if trade['accepter_receives']:
                                for asset in trade['accepter_receives']:
                                    st.markdown(f"- {asset}")
                            else:
                                st.markdown("*(Nothing)*")

                        st.divider()
            else:
                st.info("No trades found matching selection.")

    else:
        st.info("No trades found to generate matrix.")
