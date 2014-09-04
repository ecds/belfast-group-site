import networkx as nx


def annotate_graph(graph, fields=[]):
    '''Annotate a :mod:`networkx` graph with network information.

    :param graph: :class:`networkx.graph.Graph` or subclass
    :param fields: list of fields to be added to the nodes in the graph;
        can include any of: degree, in_degree, out_degree,
        betweenness_centrality, eigenvector_centrality

    :returns: a graph with the requested annotations added to each node
        in the graph
    '''

    if 'degree' in fields:
        degree = graph.degree()
    # TODO: do we need to check that graph is directional for in/out degree?
    if 'in_degree' in fields and hasattr(graph, 'in_degree'):
        in_degree = graph.in_degree()
    if 'out_degree' in fields and hasattr(graph, 'out_degree'):
        out_degree = graph.out_degree()
    if 'betweenness_centrality' in fields:
        between = nx.algorithms.centrality.betweenness_centrality(graph)
    if 'eigenvector_centrality' in fields:
        use_g = graph
        if isinstance(graph, nx.MultiDiGraph):
            use_g = nx.DiGraph(graph)
        elif isinstance(graph, nx.MultiGraph):
            use_g = nx.Graph(graph)

        eigenv = nx.algorithms.centrality.eigenvector_centrality(use_g)


    for node in graph.nodes():
        if 'degree' in fields:
            graph.node[node]['degree'] = degree[node]
        if 'in_degree' in fields and hasattr(graph, 'in_degree'):
            graph.node[node]['in_degree']= in_degree[node]
        if 'out_degree' in fields and hasattr(graph, 'out_degree'):
            graph.node[node]['out_degree']= out_degree[node]
        if 'betweenness_centrality' in fields:
            graph.node[node]['betweenness'] = between[node]
        if 'eigenvector_centrality' in fields:
            graph.node[node]['eigenvector_centrality'] = eigenv[node]

    return graph


def filter_graph(graph, min_degree):
    '''Filter a network graph by minimum degree.

    :param graph: :class:`networkx.graph.Graph` or subclass
    :param min_degree: minimum degree for nodes to be kept in the graph

    :returns: graph with only the nodes with degree higher or equal to
        the specified minimum, and all connecting edges among those nodes
    '''

    # filter a network graph by minimum degree
    nodes_to_keep = []
    degree = graph.degree()
    # iterate through the graph and identify nodes we want to keep
    for node in graph.nodes():
        if degree[node] >= min_degree:
            nodes_to_keep.append(node)

    # generate and return a subgraph with only those nodes and connecting edges
    return graph.subgraph(nodes_to_keep)
