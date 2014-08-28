import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


def make_author_graph(papers):
    G = nx.Graph()

    counts = papers.groupby('author').apply(len)
    for paper, df in papers.groupby('url'):
        authors = df['author']
        for author in authors:
            if not G.has_node(author):
                G.add_node(author)
                G.node[author]['papers'] = counts[author]

        for i, author1 in enumerate(authors):
            for author2 in authors[(i + 1):]:
                if not G.has_edge(author1, author2):
                    G.add_edge(author1, author2)
                    G.edge[author1][author2]['weight'] = 0
                G.edge[author1][author2]['weight'] += 1

    return G


def draw(G, with_labels=False, n=10, threshold=1):
    nodes = set([v for v in G if G.node[v]['papers'] >= threshold])
    subgraph = G.subgraph(nodes)
    labels = {v: v for v in subgraph if G.degree(v) >= n}

    node_color = np.array([float(G.node[v]['papers']) for v in subgraph])
    node_color = node_color - node_color.min()
    node_color = node_color / node_color.max()
    node_color = 1 - node_color

    node_size = [(G.degree(v) ** 2) * 2 for v in subgraph]

    nx.draw(
        subgraph,
        node_color=node_color,
        node_size=node_size,
        with_labels=with_labels,
        labels=labels,
        cmap=plt.cm.Reds_r,
        alpha=0.8)
