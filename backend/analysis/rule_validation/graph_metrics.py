"""
graph_metrics.py
==================
Computes graph topology metrics (Degree Centrality, Betweenness Centrality, PageRank)
for all master entities using NetworkX.
"""

import networkx as nx

def compute_graph_metrics(master_entities: list, relations: list) -> dict:
    """
    Constructs a NetworkX DiGraph from entities and relations,
    and calculates centrality & PageRank metrics for all entities.
    Returns:
        { master_id: { "degree": float, "betweenness": float, "pagerank": float } }
    """
    G = nx.DiGraph()
    
    # 1. Add all master entities as nodes
    for master in master_entities:
        mid = master.get("master_id")
        if mid:
            G.add_node(mid)
            
    # 2. Add all relations as directed edges
    for rel in relations:
        src = rel.get("source")
        tgt = rel.get("target")
        if src and tgt:
            # We add/overwrite edges. Centrality calculations are based on topology.
            G.add_edge(src, tgt)
            
    # If the graph has no nodes or edges, return empty dicts
    if G.number_of_nodes() == 0:
        return {}
        
    # 3. Compute metrics using NetworkX
    try:
        deg_cent = nx.degree_centrality(G)
    except Exception:
        deg_cent = {node: 0.0 for node in G.nodes()}
        
    try:
        bet_cent = nx.betweenness_centrality(G)
    except Exception:
        bet_cent = {node: 0.0 for node in G.nodes()}
        
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
    except Exception:
        # Fallback to pagerank with smaller max_iter or just degrees
        try:
            pagerank = nx.pagerank(G, max_iter=200)
        except Exception:
            pagerank = {node: 0.0 for node in G.nodes()}
            
    # 4. Compile metrics dictionary
    node_metrics = {}
    for node in G.nodes():
        node_metrics[node] = {
            "degree": float(round(deg_cent.get(node, 0.0), 4)),
            "betweenness": float(round(bet_cent.get(node, 0.0), 4)),
            "pagerank": float(round(pagerank.get(node, 0.0), 4))
        }
        
    return node_metrics
