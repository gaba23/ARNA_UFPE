import networkx as nx
from graphviz import Digraph

# Definindo as atividades do projeto com durações fixas
atividades_cpm = {
    "A": {"precedentes": [], "duracao": 5},  # Duração fixa
    "B": {"precedentes": ["A"], "duracao": 6},  # Duração fixa
    "C": {"precedentes": ["A"], "duracao": 5},  # Duração fixa
    "D": {"precedentes": ["B"], "duracao": 8},  # Duração fixa
    "E": {"precedentes": ["B"], "duracao": 10},  # Duração fixa
    "F": {"precedentes": ["C"], "duracao": 5},  # Duração fixa
    "G": {"precedentes": ["D", "E"], "duracao": 8},  # Duração fixa
    "H": {"precedentes": ["F"], "duracao": 5},  # Duração fixa
    "fim": {"precedentes": ["G", "H"], "duracao": 0}  # Duração zero para o nó final
}

def calcular_cpm(atividades_cpm):
    def is_edge_in_critical_path(u, v):
        return (u, v) in zip(critical_path[:-1], critical_path[1:])

    def calcular_es_ef(G):
        es = {}
        ef = {}

        # Calcular Early Start (ES) e Early Finish (EF)
        for node in nx.topological_sort(G):
            if not G.in_edges(node):  # Se não houver predecessores
                es[node] = 0
            else:
                # Calcular ES
                es[node] = max(ef[pred] for pred in G.predecessors(node))
            # Atualizar ef
            ef[node] = es[node] + G.nodes[node]['duracao']

        return es, ef

    atividades = {}
    for atividade, dados in atividades_cpm.items():
        atividades[atividade] = {
            "precedentes": dados["precedentes"],
            "duracao": dados["duracao"]
        }

    # Criar o grafo direcionado
    G = nx.DiGraph()

    # Adicionar os nós e as arestas ao grafo
    for atividade, info in atividades.items():
        G.add_node(atividade, duracao=info['duracao'])
        for precedente in info['precedentes']:
            G.add_edge(precedente, atividade, weight=info['duracao'])

    # Calcular o caminho crítico
    critical_path = nx.dag_longest_path(G)
    critical_path.append('fim')

    es, ef = calcular_es_ef(G)

    ls = {}
    for node in reversed(list(nx.topological_sort(G))):
        if node == 'fim':
            ls[node] = es[node]  # O LS da atividade 'fim' é igual ao seu ES
        elif not G.out_edges(node):
            ls[node] = ls['fim'] - G.nodes[node]['duracao']
        else:
            ls[node] = min(ls[succ] for succ in G.successors(node)) - G.nodes[node]['duracao']

    lf = {node: ls[node] + G.nodes[node]['duracao'] for node in G.nodes()}

    # Desenhar o grafo com Graphviz
    dot = Digraph()
    dot.attr(rankdir='LR')  # Definindo o layout horizontal da esquerda para a direita
    for node in G.nodes():
        duracao = round(G.nodes[node]['duracao'], 4)
        es_node = round(es[node], 4)
        ef_node = round(ef[node], 4)
        ls_node = round(ls[node], 4)
        lf_node = round(lf[node], 4)

        # Ajustar valores negativos próximos de zero
        if ls_node == -0.0 or ls_node < 0.0:
            ls_node = 0.0

        dot.node(node, shape='box', label=f"{node}\nDuração: {duracao}\nES: {es_node}/ EF:{ef_node}\nLS: {ls_node} /LF: {lf_node}")

    for edge in G.edges():
        if is_edge_in_critical_path(edge[0], edge[1]):
            dot.edge(edge[0], edge[1], color='red')
        else:
            dot.edge(edge[0], edge[1])

    dot.render('resultadosCpm/atividades_cpm', format='png', cleanup=True)

    imagem = ["atividades_cpm.png"]
    return imagem

calcular_cpm(atividades_cpm)
