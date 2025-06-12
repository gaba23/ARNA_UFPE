import networkx as nx
from graphviz import Digraph
import matplotlib.pyplot as plt
import pandas as pd

# Definindo as atividades do projeto com durações fixas
# atividades_cpm = {
#     "A": {"precedentes": [], "duracao": 5},  # Duração fixa
#     "B": {"precedentes": ["A"], "duracao": 6},  # Duração fixa
#     "C": {"precedentes": ["A"], "duracao": 5},  # Duração fixa
#     "D": {"precedentes": ["B"], "duracao": 8},  # Duração fixa
#     "E": {"precedentes": ["B"], "duracao": 10},  # Duração fixa
#     "F": {"precedentes": ["C"], "duracao": 5},  # Duração fixa
#     "G": {"precedentes": ["D", "E"], "duracao": 8},  # Duração fixa
#     "H": {"precedentes": ["F"], "duracao": 5},  # Duração fixa
#     "fim": {"precedentes": ["G", "H"], "duracao": 0}  # Duração zero para o nó final
# }


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

    # Cálculo das folgas 
    folga = {node: ls[node] - es[node] for node in G.nodes()}

    # Desenhar o grafo com Graphviz
    dot = Digraph()
    dot.attr(rankdir='LR')  # Definindo o layout horizontal da esquerda para a direita
    for node in G.nodes():
        duracao = round(G.nodes[node]['duracao'], 2)
        es_node = round(es[node], 2)
        ef_node = round(ef[node], 2)
        ls_node = round(ls[node], 2)
        lf_node = round(lf[node], 2)
        folga_node = round(folga[node], 2)

        # Ajustar valores negativos próximos de zero
        if ls_node == -0.0 or ls_node < 0.0:
            ls_node = 0.0
        if folga_node == -0.0 or folga_node < 0.0:
            folga_node = 0.0

        dot.node(node, shape='box', label=f"{node}\nDuração: {duracao}\nES: {es_node}/ EF:{ef_node}\nLS: {ls_node} /LF: {lf_node}\nSlack: {folga_node}")

    for edge in G.edges():
        if is_edge_in_critical_path(edge[0], edge[1]):
            dot.edge(edge[0], edge[1], color='red')
        else:
            dot.edge(edge[0], edge[1])

    dot.render('resultadosCpm/atividades_cpm', format='png', cleanup=True)

    imagem = ["atividades_cpm.png"]

    # Criar gráfico de Gantt
    fig, ax = plt.subplots(figsize=(10, 6))

    y_labels = []
    y_pos = []
    cores = []
    start_times = []
    durations = []

    for i, node in enumerate(sorted(G.nodes(), key=lambda n: es[n])):
        if node == 'fim':
            continue  # Ignorar nó artificial 'fim'

        y_labels.append(node)
        y_pos.append(i)
        start_times.append(es[node])
        durations.append(G.nodes[node]['duracao'])
        if node in critical_path:
            cores.append('red')
        else:
            cores.append('skyblue')

    ax.barh(y_pos, durations, left=start_times, color=cores, edgecolor='black')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Tempo")
    ax.set_title("Gráfico de Gantt - CPM")

    # Inverter eixo Y para desenhar de cima para baixo
    ax.invert_yaxis()

    # Adiciona rótulos nas barras
    for i in range(len(y_pos)):
        ax.text(start_times[i] + durations[i] / 2, y_pos[i], f"{start_times[i]} → {start_times[i] + durations[i]}", 
                va='center', ha='center', color='black', fontsize=8)

    plt.tight_layout()
    plt.savefig('resultadosCpm/gantt_cpm.png')
    plt.close()

    imagem.append("gantt_cpm.png")

    # EXCEL
    atv_ignore = ['inicio', 'fim']  # ignorar atividades placeholders

    resumo_data = []
    for node in G.nodes():
        if node in atv_ignore:
            continue

        resumo_data.append({
            "Atividade": node,
            "Duração": G.nodes[node]['duracao'],
            "ES": es[node],
            "EF": ef[node],
            "LS": ls[node],
            "LF": lf[node],
            "Folga": folga[node],
            "Caminho Crítico": "Sim" if node in critical_path else "Não"
        })

    df_resumo = pd.DataFrame(resumo_data)
    df_caminho = pd.DataFrame({"Caminho Crítico": [a for a in critical_path if a != 'fim']})
    df_folgas = df_resumo[df_resumo["Folga"] > 0][["Atividade", "Folga"]]

    # Formatar dataframes
    df_caminho = pd.DataFrame({"Caminho Crítico": [a for a in critical_path if a not in atv_ignore]})
    df_folgas = df_resumo[df_resumo["Folga"] > 0][["Atividade", "Folga"]]

    # Escrever arquivo
    with pd.ExcelWriter("./resultadosCpm/relatorio_cpm.xlsx", engine='openpyxl') as writer:
        df_resumo.to_excel(writer, sheet_name="Resumo das Atividades", index=False)
        df_caminho.to_excel(writer, sheet_name="Caminho Crítico", index=False)
        df_folgas.to_excel(writer, sheet_name="Folgas", index=False)
    
    return imagem
