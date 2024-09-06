import networkx as nx
from graphviz import Digraph

atividades_pert = {
        "A": {"precedentes": [], "t_otimista": 2, "t_pessimista": 8, "t_provavel": 5},
        "B": {"precedentes": ["A"], "t_otimista": 3, "t_pessimista": 10, "t_provavel": 6},
        "C": {"precedentes": ["A"], "t_otimista": 1, "t_pessimista": 4, "t_provavel": 5},
        "D": {"precedentes": ["B"], "t_otimista": 4, "t_pessimista": 6, "t_provavel": 8},
        "E": {"precedentes": ["B"], "t_otimista": 8, "t_pessimista": 12, "t_provavel": 10},
        "F": {"precedentes": ["C"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
        "G": {"precedentes": ["D", "E"], "t_otimista": 7, "t_pessimista": 11, "t_provavel": 8},
        "H": {"precedentes": ["F"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
        "fim": {"precedentes": ["G", "H"], "duracao": 0}
}

def calcular_pert(atividades_pert):
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

        # Atualizar ES para atividades sem predecessores
        for node in G.nodes():
            if not G.predecessors(node):
                es[node] = 0

        return es, ef
    
    atividades = {}
    for atividade, dados in atividades_pert.items():
        if atividade != "fim":
            t_calculado = (dados["t_otimista"] + dados["t_pessimista"] + dados["t_provavel"] * 4) / 6
            atividades[atividade] = {
                "precedentes": dados["precedentes"],
                "duracao": t_calculado
            }
        else:
            atividades[atividade] = dados

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
            ls[node] = ls['fim'] - G.nodes[node]['duracao']  # O LS das atividades que precedem a atividade 'fim' é igual ao LS da atividade 'fim' - duração da atividade
        else:
            ls[node] = min(ls[succ] for succ in G.successors(node)) - G.nodes[node]['duracao']

    lf = {node: ls[node] + G.nodes[node]['duracao'] for node in G.nodes()}

    #print('valor es')
    #print(es)
    #print('valor ef')
    #print(ef)
    #print('valor ls')
    #print(ls)
    #print('valor lf')
    #print(lf)

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

    dot.render('resultadosPert/atividades_pert', format='png', cleanup=True)

    imagem = ["atividades_pert.png"]
    return imagem
