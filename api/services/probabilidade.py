from scipy.stats import norm
import numpy as np
import networkx as nx

# Cálculo calculadora de probabilidade
    # Obter durações das atividades no caminho crítico (excluindo 'fim')
def calcular_probabilidade(G, critical_path, atividades_pert, t_programado):
    duracoes_criticas = [
    G.nodes[atividade]['duracao']
    for atividade in critical_path if atividade != 'fim'
    ]

        # Média do projeto = soma das durações no caminho crítico
    media_projeto = sum(duracoes_criticas)
    #print(media_projeto)

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
    #print(desvio_padrao_projeto)

    def calcular_probabilidade(t_programado):
        return norm.cdf(t_programado, loc=media_projeto, scale=desvio_padrao_projeto)
    
    # Valor da probabilidade
    var_prob = calcular_probabilidade(t_progamado)
    #print(var_prob)