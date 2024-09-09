import networkx as nx
import matplotlib.pyplot as plt

# Definindo as atividades e seus precedentes
atividades_cpm = {
    "A": {"precedentes": [], "duracao": 2},
    "B": {"precedentes": ["A"], "duracao": 6},
    "C": {"precedentes": ["A"], "duracao": 4},
    "D": {"precedentes": ["B"], "duracao": 5},
    "E": {"precedentes": ["B"], "duracao": 10},
    "F": {"precedentes": ["C"], "duracao": 9},
    "G": {"precedentes": ["D", "E"], "duracao": 8},
    "H": {"precedentes": ["F"], "duracao": 3},
    "fim": {"precedentes": ["G", "H"], "duracao": 0}
}

# Criando o grafo para a análise CPM
G = nx.DiGraph()

# Adicionando nós e arestas
for atividade, dados in atividades_cpm.items():
    for precedente in dados["precedentes"]:
        G.add_edge(precedente, atividade, weight=dados["duracao"])

# Calculando o caminho crítico
caminho_critico = nx.dag_longest_path(G, weight='weight')
caminho_critico_duracao = nx.dag_longest_path_length(G, weight='weight')

# Visualização do grafo
pos = nx.planar_layout(G)
plt.figure(figsize=(10, 8))

# Desenho do grafo
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=3000, font_size=12, font_weight='bold', arrows=True)
nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, edge_color='gray')

# Destacando o caminho crítico
nx.draw_networkx_edges(G, pos, edgelist=list(zip(caminho_critico, caminho_critico[1:])), width=4, edge_color='red')

plt.title(f'Caminho Crítico: {" -> ".join(caminho_critico)} (Duração: {caminho_critico_duracao} dias)')
plt.show()

##############################################################################################################################

import networkx as nx
import matplotlib.pyplot as plt

# Atividades e suas propriedades
atividades_cpm = {
    "A": {"precedentes": [], "duracao": 2},
    "B": {"precedentes": ["A"], "duracao": 6},
    "C": {"precedentes": ["A"], "duracao": 4},
    "D": {"precedentes": ["B"], "duracao": 5},
    "E": {"precedentes": ["B"], "duracao": 10},
    "F": {"precedentes": ["C"], "duracao": 9},
    "G": {"precedentes": ["D", "E"], "duracao": 8},
    "H": {"precedentes": ["F"], "duracao": 3},
    "fim": {"precedentes": ["G", "H"], "duracao": 0}
}

# Função para calcular datas mais cedo
def calcular_datas_mais_cedo(atividades):
    datas_inicio = {}
    datas_termino = {}
    for atividade, detalhes in atividades.items():
        if detalhes["precedentes"]:
            datas_inicio[atividade] = max(datas_termino[p] for p in detalhes["precedentes"])
        else:
            datas_inicio[atividade] = 0
        datas_termino[atividade] = datas_inicio[atividade] + detalhes["duracao"]
    return datas_inicio, datas_termino

# Função para calcular datas mais tarde
def calcular_datas_mais_tarde(atividades, datas_termino_mais_cedo):
    datas_inicio_tarde = {}
    datas_termino_tarde = {}
    for atividade in reversed(list(atividades.keys())):
        if atividades[atividade]["precedentes"]:
            datas_termino_tarde[atividade] = min(datas_inicio_tarde[s] for s in atividades if atividade in atividades[s]["precedentes"])
        else:
            datas_termino_tarde[atividade] = datas_termino_mais_cedo["fim"]
        datas_inicio_tarde[atividade] = datas_termino_tarde[atividade] - atividades[atividade]["duracao"]
    return datas_inicio_tarde, datas_termino_tarde

# Cálculo das datas
datas_inicio_mais_cedo, datas_termino_mais_cedo = calcular_datas_mais_cedo(atividades_cpm)
datas_inicio_mais_tarde, datas_termino_mais_tarde = calcular_datas_mais_tarde(atividades_cpm, datas_termino_mais_cedo)

# Determinação das folgas e do caminho crítico
caminho_critico = []
for atividade in atividades_cpm:
    folga = datas_inicio_mais_tarde[atividade] - datas_inicio_mais_cedo[atividade]
    if folga == 0:
        caminho_critico.append(atividade)

# Visualização do diagrama de rede
G = nx.DiGraph()

for atividade, detalhes in atividades_cpm.items():
    for pre in detalhes["precedentes"]:
        G.add_edge(pre, atividade)

pos = nx.spring_layout(G)
nx.draw_networkx(G, pos, with_labels=True, node_size=3000, node_color='lightblue')
nx.draw_networkx_edges(G, pos, edgelist=[(caminho_critico[i], caminho_critico[i+1]) for i in range(len(caminho_critico)-1)], edge_color='r', width=3)

plt.title("Diagrama de Rede CPM com Caminho Crítico")
plt.show()

