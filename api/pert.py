import csv
import networkx as nx
from graphviz import Digraph
import math
import matplotlib.pyplot as plt
#import matplotlib.patches as mpatches
import numpy as np
from services.arrownodediagram import create_arrow_diagram as encontrar_caminhos_seta
#from scipy.stats import norm

# atividades_pert = {
#         "A": {"precedentes": [], "t_otimista": 2, "t_pessimista": 8, "t_provavel": 5},
#         "B": {"precedentes": ["A"], "t_otimista": 3, "t_pessimista": 10, "t_provavel": 6},
#         "C": {"precedentes": ["A"], "t_otimista": 1, "t_pessimista": 4, "t_provavel": 5},
#         "D": {"precedentes": ["B"], "t_otimista": 4, "t_pessimista": 6, "t_provavel": 8},
#         "E": {"precedentes": ["B"], "t_otimista": 8, "t_pessimista": 12, "t_provavel": 10},
#         "F": {"precedentes": ["C"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
#         "G": {"precedentes": ["D", "E"], "t_otimista": 7, "t_pessimista": 11, "t_provavel": 8},
#         "H": {"precedentes": ["F"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
#         "fim": {"precedentes": ["G", "H"], "duracao": 0}
# }

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
            t_o = dados["t_otimista"]
            t_p = dados["t_pessimista"]
            t_m = dados["t_provavel"]

            # Verificação de consistência dos dados
            if t_p == t_o or not (t_o <= t_m <= t_p):
                # Usa uma média simples como fallback
                t_calculado = (t_o + 4 * t_m + t_p) / 6
            else:
                # Calculando os parâmetros alpha e beta da distribuição beta
                alpha = 1 + 4 * (t_m - t_o) / (t_p - t_o)
                beta_param = 1 + 4 * (t_p - t_m) / (t_p - t_o)

                # Segurança extra para evitar valores inválidos
                if alpha <= 0 or beta_param <= 0:
                    t_calculado = (t_o + 4 * t_m + t_p) / 6
                else:
                    beta_random = np.random.beta(alpha, beta_param)
                    t_calculado = beta_random * (t_p - t_o) + t_o

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

    #Média e desvio padrão para a probabilidade
    #Média
    tempo_total = lf['fim']
    
    # Desvio padrão do projeto
    desvios_criticos = []
    for atividade in critical_path:
        if atividade == 'fim':
            continue
        dados = atividades_pert[atividade]
        sigma = (dados["t_pessimista"] - dados["t_otimista"]) / 6
        desvios_criticos.append(sigma)

    # Desvio padrão total do caminho crítico
    desvio_padrao_projeto = np.sqrt(np.sum(np.square(desvios_criticos)))


    # Cálculo das folgas 
    folga = {node: ls[node] - es[node] for node in G.nodes()}

    # GRAFO
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

        dot.node(node, shape='box', label=f"{node}\nDuration: {duracao}\nES: {es_node}/ EF:{ef_node}\nLS: {ls_node} /LF: {lf_node}\nSlack: {folga_node}")

    for edge in G.edges():
        if is_edge_in_critical_path(edge[0], edge[1]):
            dot.edge(edge[0], edge[1], color='red')
        else:
            dot.edge(edge[0], edge[1])

    dot.render('resultadosPert/atividades_pert', format='png', cleanup=True)

    imagem = ["atividades_pert.png"]

    # DIAGRAMA ATIVIDADE NA SETA
    def is_critical(atividade, critical_path):
        return 'y' if atividade in critical_path else 'n'

    with open('./temp/pertDataset.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ActivityId", "Predecessors", "Crucial"])

        for atividade, dados in atividades.items():
            if atividade == 'inicio':
                continue  # ignorar atividade início

            pred = [
                p for p in dados['precedentes'] if p != 'inicio'  # apagar atividade início dos predecessores
            ]
            pred_str = " ".join(pred)
            critico = is_critical(atividade, critical_path)
            if atividade == 'fim':
                writer.writerow([int(len(atividades) - 1), pred_str, critico])
            else:
                writer.writerow([atividade, pred_str, critico])

    encontrar_caminhos_seta('./temp/pertDataset.csv', './resultadosPert/diagrama_na_seta')

    # GANTT
    fig, ax = plt.subplots(figsize=(10, 6))

    # Parâmetros visuais
    altura_barra = 0.4  
    offset_seta = 0.2

    y_labels = []
    y_ticks = []
    cores = []
    node_positions = {}

    for i, node in enumerate(sorted(G.nodes(), key=lambda n: es[n])):
        if node in ['início', 'fim']:
            continue  # Ignorar nós artificial 'fim'

        inicio = es[node]
        duracao = G.nodes[node]['duracao']
        cor = 'red' if node in critical_path else 'skyblue'

        # Desenha a barra manualmente com altura personalizada
        ax.broken_barh(
            [(inicio, duracao)],
            (i - altura_barra / 2, altura_barra),
            facecolors=cor,
            edgecolors='black'
        )

        y_labels.append(node)
        y_ticks.append(i)
        node_positions[node] = (inicio, i)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Tempo")
    ax.set_title("Gráfico de Gantt - PERT")

    # Inverter eixo Y para desenhar de cima para baixo
    ax.invert_yaxis()

    # Adiciona setas entre as atividades baseadas nas dependências do grafo
    for predecessor, successor in G.edges():
        if predecessor == 'início':
            continue
        if predecessor in node_positions and successor in node_positions:
            x_start, y_start = node_positions[predecessor]
            x_end, y_end = node_positions[successor]
            x_start += G.nodes[predecessor]['duracao'] + offset_seta
            x_end -= offset_seta

            ax.annotate(
                '',
                xy=(x_end, y_end),
                xytext=(x_start, y_start),
                arrowprops=dict(
                    color='black',
                    arrowstyle='->',
                    mutation_scale=10,
                    lw=1.25,
                    linestyle='dotted',
                    connectionstyle='angle', 
                ),
                annotation_clip=False
            )

    plt.tight_layout()
    plt.savefig('resultadosPERT/gantt_pert.png')
    plt.close()

    imagem.append("gantt_pert.png")

    # TABELA DE ARESTAS
    headers = ["Atividade", "Precedentes", "T. Otimista", "T. Pessimista", "T. Provável", "T. Esperado", "DP", "Variância"]
    rows = []

    for atividade, dados in atividades_pert.items():
        if atividade in ["inicio", "fim"]:  # ignora
            continue

        t_o = dados["t_otimista"]
        t_p = dados["t_pessimista"]
        t_m = dados["t_provavel"]

        t_esperado = (t_o + 4 * t_m + t_p) / 6
        dp = (t_p - t_o) / 6
        variancia = dp ** 2

        precedentes_filtrados = [p for p in dados["precedentes"] if p != "inicio"]  # filtra atividade inicial dos precedentes
        precedentes = ", ".join(precedentes_filtrados) if precedentes_filtrados else "-"

        rows.append([
            atividade,
            precedentes,
            round(t_o, 2),
            round(t_p, 2),
            round(t_m, 2),
            round(t_esperado, 2),
            round(dp, 2),
            round(variancia, 2)
        ])

    # Criar png
    fig, ax = plt.subplots(figsize=(12, max(2, len(rows) * 0.5)))
    ax.axis('off')  # esconde os eixos

    table = ax.table(cellText=rows, colLabels=headers, loc='center', cellLoc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    plt.tight_layout()
    plt.savefig("resultadosPert/tabela_arestas.png")
    plt.close()

    imagem.append("tabela_arestas.png")

    critical_path = critical_path[1:-1]
    #print(critical_path)

    return imagem, critical_path, tempo_total, desvio_padrao_projeto