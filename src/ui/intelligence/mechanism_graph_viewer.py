"""
Mechanism Graph Viewer - Visualize drug → target → pathway → AE graphs
"""

import streamlit as st
from typing import Dict, Any


def render_mechanism_graph(graph: Dict[str, Any]):
    """
    Render mechanism graph visualization.
    
    Args:
        graph: Graph structure with nodes and edges
    """
    st.subheader("🔬 Mechanism Graph")
    
    if not graph or "nodes" not in graph:
        st.warning("No graph data available")
        return
    
    # Build Graphviz DOT string
    dot_lines = ["digraph G {"]
    dot_lines.append('    rankdir=LR;')
    dot_lines.append('    node [shape=box, style=rounded];')
    
    # Add nodes with type-based styling
    node_styles = {
        "drug": "fillcolor=lightblue, color=blue",
        "target": "fillcolor=lightgreen, color=green",
        "pathway": "fillcolor=lightyellow, color=orange",
        "ae": "fillcolor=lightcoral, color=red"
    }
    
    for node in graph["nodes"]:
        node_id = node["id"].replace('"', '\\"')
        node_type = node.get("type", "unknown")
        node_label = node.get("label", node_id)
        style = node_styles.get(node_type, "")
        
        dot_lines.append(f'    "{node_id}" [label="{node_label}", {style}];')
    
    # Add edges
    for edge in graph.get("edges", []):
        source = edge["source"].replace('"', '\\"')
        target = edge["target"].replace('"', '\\"')
        edge_type = edge.get("type", "")
        label = f' [label="{edge_type}"]' if edge_type else ""
        dot_lines.append(f'    "{source}" -> "{target}"{label};')
    
    dot_lines.append("}")
    dot_string = "\n".join(dot_lines)
    
    # Render graph
    try:
        st.graphviz_chart(dot_string)
    except Exception as e:
        st.error(f"Error rendering graph: {e}")
        st.code(dot_string, language="dot")

