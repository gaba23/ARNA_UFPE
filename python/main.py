import random
import numpy as np
import graphviz
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt

def simulacao_montecarlo():
    atividades_pert = {
        "1": {"precedentes": [], "tipo": "beta_pert", "t_otimista": 2, "t_provavel": 5, "t_pessimista": 8, "custo": 0, "descricao": "descrição da atividade"},
        "2": {"precedentes": ["1"], "tipo": "triangular", "t_minimo": 3, "t_moda": 6, "t_maximo": 10, "custo": 0, "descricao": "descrição da atividade"},
        "3": {"precedentes": ["1"], "tipo": "uniforme", "t_minimo": 1, "t_maximo": 4, "custo": 0, "descricao": "descrição da atividade"},
        "4": {"precedentes": ["2"], "tipo": "normal", "t_otimista": 4, "t_media": 6, "t_pessimista": 8, "custo": 0, "descricao": "descrição da atividade"},
        "5": {"precedentes": ["2"], "tipo": "beta_pert", "t_otimista": 8, "t_provavel": 10, "t_pessimista": 12, "custo": 0, "descricao": "descrição da atividade"},
        "6": {"precedentes": ["3"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0, "descricao": "descrição da atividade"},
        "7": {"precedentes": ["4", "5"], "tipo": "beta_pert", "t_otimista": 7, "t_provavel": 8, "t_pessimista": 11, "custo": 0, "descricao": "descrição da atividade"},
        "8": {"precedentes": ["6"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0, "descricao": "descrição da atividade"},
        "fim": {"precedentes": ["7", "8"], "tipo": "beta_pert", "duracao": 0, "custo": 0, "descricao": "descrição da atividade"}
    }

    riscos = {
        "A": {"probabilidade": 0.5, "tipo": "triangular", "atividades_afetadas": ["1"], "atraso_minimo": 3, "atraso_medio": 4, "atraso_maximo": 5},
        "B": {"probabilidade": 0.3, "tipo": "uniforme", "atividades_afetadas": ["2", "3"], "atraso_minimo": 3, "atraso_maximo": 5}
    }

    precedentes_atividades = {atividade: detalhes["precedentes"] for atividade, detalhes in atividades_pert.items()}

    riscos_ocorridos = {risco: [] for risco in riscos}
    tempos_riscos = {risco: [] for risco in riscos}

    mapa_atividades = {atividade: i + 2 for i, atividade in enumerate(atividades_pert.keys())}
    mapa_atividades["inicio"] = 1

    atividades_convertidas = []

    for atividade, detalhes in atividades_pert.items():
        no_final = mapa_atividades[atividade]
        precedentes = detalhes.pop("precedentes", [])
        for precedente in precedentes:
            no_inicial = mapa_atividades[precedente]
            atividades_convertidas.append({
                "no_inicial": no_inicial,
                "no_final": no_final,
                **detalhes
            })
        if not precedentes:
            atividades_convertidas.append({
                "no_inicial": 1,
                "no_final": no_final,
                **detalhes
            })

    grafo = defaultdict(list)
    for atividade in atividades_convertidas:
        no_inicial = atividade["no_inicial"]
        no_final = atividade["no_final"]
        grafo[no_inicial].append(no_final)

    dot = graphviz.Digraph(comment='Diagrama de Atividades', format='png')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='rectangle')

    for atividade, no in mapa_atividades.items():
        dot.node(str(no), atividade)

    for no_inicial, nos_finais in grafo.items():
        for no_final in nos_finais:
            dot.edge(str(no_inicial), str(no_final))

    dot.render('diagrama_atividades', view=True)

    def encontrar_caminhos(grafo, inicio, fim, caminho=[]):
        caminho = caminho + [inicio]
        if inicio == fim:
            return [caminho]
        if inicio not in grafo:
            return []
        caminhos = []
        for no in grafo[inicio]:
            if no not in caminho:
                novos_caminhos = encontrar_caminhos(grafo, no, fim, caminho)
                for novo_caminho in novos_caminhos:
                    caminhos.append(novo_caminho)
        return caminhos

    def calcular_duracao_caminho(caminho, atividades_convertidas, duracoes_atividades):
        duracao = 0
        for i in range(len(caminho) - 1):
            no_inicial = caminho[i]
            no_final = caminho[i + 1]
            for atividade in atividades_convertidas:
                if atividade["no_inicial"] == no_inicial and atividade["no_final"] == no_final:
                    if "duracao" in atividade:
                        duracao_atividade = atividade["duracao"]
                    else:
                        tipo = atividade["tipo"]
                        if tipo == "beta_pert":
                            t_o = atividade["t_otimista"]
                            t_p = atividade["t_pessimista"]
                            t_m = atividade["t_provavel"]

                            alpha = 1 + 4 * (t_m - t_o) / (t_p - t_o)
                            beta = 1 + 4 * (t_p - t_m) / (t_p - t_o)

                            beta_random = np.random.beta(alpha, beta)
                            duracao_atividade = beta_random * (t_p - t_o) + t_o
                        elif tipo == "triangular":
                            t_min = atividade["t_minimo"]
                            t_mode = atividade["t_moda"]
                            t_max = atividade["t_maximo"]
                            duracao_atividade = np.random.triangular(t_min, t_mode, t_max)
                        elif tipo == "uniforme":
                            t_min = atividade["t_minimo"]
                            t_max = atividade["t_maximo"]
                            duracao_atividade = random.uniform(t_min, t_max)
                        elif tipo == "normal":
                            mu = atividade["t_media"]
                            sigma = (atividade["t_pessimista"] - atividade["t_otimista"]) / 6
                            duracao_atividade = np.random.normal(mu, sigma)
                    duracao += duracao_atividade
                    duracoes_atividades[atividade["no_final"] - 2] = duracao_atividade

                    for risco, detalhes in riscos.items():
                        ocorreu = random.random() < detalhes["probabilidade"]
                        riscos_ocorridos[risco].append(ocorreu)
                        if ocorreu:
                            atraso_total = 0
                            for atividade in detalhes["atividades_afetadas"]:
                                index_atividade = mapa_atividades[atividade] - 2
                                if detalhes["tipo"] == "triangular":
                                    atraso = np.random.triangular(detalhes["atraso_minimo"], detalhes["atraso_medio"], detalhes["atraso_maximo"])
                                elif detalhes["tipo"] == "uniforme":
                                    atraso = random.uniform(detalhes["atraso_minimo"], detalhes["atraso_maximo"])
                                duracoes_atividades[index_atividade] += atraso
                                atraso_total += atraso
                            tempos_riscos[risco].append(atraso_total)
                        else:
                            tempos_riscos[risco].append(0)

                    break
        return duracao

    num_interacoes = 1000
    caminhos = encontrar_caminhos(grafo, mapa_atividades["inicio"], mapa_atividades['fim'])

    contagem_caminhos_criticos = {tuple(caminho): 0 for caminho in caminhos}
    contagem_atividades_criticas = {atividade: 0 for atividade in atividades_pert.keys()}

    resultados_atividades = []
    resultados_caminhos = []
    resultados_caminhos_criticos = []
    duracoes_projeto = []

    for iteracao in range(num_interacoes):
        duracoes_atividades = [0] * len(atividades_pert)
        duracoes_caminhos = []
        caminho_critico = None
        duracao_maxima = 0

        for caminho in caminhos:
            duracao = calcular_duracao_caminho(caminho, atividades_convertidas, duracoes_atividades)
            duracoes_caminhos.append(duracao)
            if duracao > duracao_maxima:
                duracao_maxima = duracao
                caminho_critico = caminho

        resultados_caminhos.append(duracoes_caminhos)
        duracoes_projeto.append(duracao_maxima)
        if caminho_critico:
            contagem_caminhos_criticos[tuple(caminho_critico)] += 1

        for i, duracao_atividade in enumerate(duracoes_atividades):
            if duracao_atividade > 0:
                atividade = [k for k, v in mapa_atividades.items() if v - 2 == i][0]
                contagem_atividades_criticas[atividade] += 1
                resultados_atividades.append({
                    "atividade": atividade,
                    "duracao": duracao_atividade
                })

    resultados_caminhos_criticos.append({
        "caminho_critico": caminho_critico,
        "frequencia": contagem_caminhos_criticos[tuple(caminho_critico)] / num_interacoes
    })

    df_resultados_atividades = pd.DataFrame(resultados_atividades)
    df_resultados_caminhos = pd.DataFrame(resultados_caminhos, columns=[f'Caminho_{i+1}' for i in range(len(caminhos))])
    df_resultados_caminhos_criticos = pd.DataFrame(resultados_caminhos_criticos)

    planilha = pd.ExcelWriter('resultados_simulacao.xlsx', engine='xlsxwriter')
    df_resultados_atividades.to_excel(planilha, sheet_name='Resultados_Atividades', index=False)
    df_resultados_caminhos.to_excel(planilha, sheet_name='Resultados_Caminhos', index=False)
    df_resultados_caminhos_criticos.to_excel(planilha, sheet_name='Resultados_Caminhos_Criticos', index=False)
    planilha.save()

    plt.hist(duracoes_projeto, bins=30, edgecolor='black')
    plt.title('Distribuição da Duração do Projeto')
    plt.xlabel('Duração (unidades de tempo)')
    plt.ylabel('Frequência')
    plt.grid(True)
    plt.savefig('distribuicao_duracao_projeto.png')
    plt.show()

    return {
        'planilha': 'resultados_simulacao.xlsx',
        'imagem_duracao_projeto': 'distribuicao_duracao_projeto.png'
    }
