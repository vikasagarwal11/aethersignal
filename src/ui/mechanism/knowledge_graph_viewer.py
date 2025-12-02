"""
Knowledge Graph Viewer - Interactive KG visualization
"""

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def render_kg(graph: Dict[str, Any], layout: str = "spring"):
    """
    Render knowledge graph visualization.
    
    Args:
        graph: Graph dictionary with nodes and edges
        layout: Layout algorithm (spring, circular, hierarchical)
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    if not nodes:
        st.info("No graph data to display.")
        return
    
    try:
        G = nx.DiGraph()
        
        # Add nodes
        for n in nodes:
            node_id = n.get("id", str(n))
            node_type = n.get("type", "unknown")
            G.add_node(node_id, type=node_type, label=n.get("label", node_id))
        
        # Add edges
        for e in edges:
            source = e.get("source")
            target = e.get("target")
            if source and target:
                edge_type = e.get("type", "related")
                weight = e.get("weight", 1.0)
                G.add_edge(source, target, type=edge_type, weight=weight)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Choose layout
        if layout == "spring":
            pos = nx.spring_layout(G, seed=42, k=1, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "hierarchical":
            try:
                pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
            except:
                pos = nx.spring_layout(G, seed=42)
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Color nodes by type
        node_colors = []
        for node in G.nodes():
            node_type = G.nodes[node].get("type", "unknown")
            color_map = {
                "drug": "#3b82f6",
                "reaction": "#ef4444",
                "pathway": "#22c55e",
                "mechanism": "#f59e0b",
                "target": "#8b5cf6"
            }
            node_colors.append(color_map.get(node_type, "#94a3b8"))
        
        # Draw graph
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_size=2000,
            node_color=node_colors,
            font_size=8,
            font_weight="bold",
            arrows=True,
            arrowsize=20,
            edge_color="#cbd5e1",
            width=2,
            ax=ax
        )
        
        ax.set_title("Mechanistic Knowledge Graph", fontsize=14, fontweight="bold")
        plt.tight_layout()
        
        st.pyplot(fig)
        plt.close(fig)
        
        # Graph statistics
        with st.expander("Graph Statistics"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Nodes", G.number_of_nodes())
            col2.metric("Edges", G.number_of_edges())
            col3.metric("Density", f"{nx.density(G):.3f}")
            
    except Exception as e:
        logger.error(f"Graph rendering error: {e}")
        st.error(f"Error rendering graph: {e}")
        st.json(graph)


def render_kg_simple(nodes: List[str], edges: List[tuple]):
    """
    Render simple graph from node and edge lists.
    
    Args:
        nodes: List of node names
        edges: List of (source, target) tuples
    """
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(G, seed=42)
    
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1500,
        node_color="#93c5fd",
        font_size=10,
        arrows=True,
        ax=ax
    )
    
    st.pyplot(fig)
    plt.close(fig)

