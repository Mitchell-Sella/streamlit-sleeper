import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import networkx as nx

def show(analyzer):
    st.header("Trade Network")
    st.markdown("This network visualizes trades between teams. Thicker lines indicate more trades.")

    G = analyzer.build_trade_network()

    if len(G.nodes) == 0:
        st.warning("No trades found in this league/season.")
        return

    nodes = []
    edges = []

    # Calculate degree for node sizing
    degrees = dict(G.degree)

    for node_id in G.nodes:
        # Node properties
        node_label = str(G.nodes[node_id].get('label', node_id))
        size = 20 + (degrees.get(node_id, 0) * 5)
        nodes.append(Node(id=node_id, label=node_label, size=size, color="#FF4136"))

    for u, v in G.edges:
        edge_data = G[u][v]
        count = edge_data.get('count', 1)
        # Edge properties
        edges.append(Edge(source=u, target=v, label=str(count), width=count*2, color="#0074D9"))

    config = Config(width=800,
                    height=600,
                    directed=False,
                    physics=True,
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A7A6",
                    collapsible=True)

    return_value = agraph(nodes=nodes, edges=edges, config=config)
