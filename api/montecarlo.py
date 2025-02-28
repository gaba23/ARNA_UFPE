import random
import numpy as np
import graphviz
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import glob
import networkx as nx
import os
import csv
from scipy import stats
from scipy.interpolate import make_interp_spline, BSpline
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from arrownodediagram import create_arrow_diagram as encontrar_caminhos_seta


def simular_montecarlo(atividades_pert, riscos, num_iteracoes):

    precedentes_atividades = {atividade: detalhes["precedentes"] for atividade, detalhes in atividades_pert.items()}
    riscos_ocorridos = {risco: [] for risco in riscos}

    custo_fixo = {atividade: detalhes["custo_fix"] for atividade, detalhes in atividades_pert.items()}
    custo_variavel = {atividade: detalhes["custo_un"] for atividade, detalhes in atividades_pert.items()}
 
    end_atv_key = str(len(atividades_pert))
    end_atv_fix_value = custo_fixo.get("fim")
    end_atv_var_value = custo_variavel.get("fim")

    custo_fixo.pop('fim')
    custo_variavel.pop('fim')

    custo_fixo.update({end_atv_key: end_atv_fix_value})
    custo_variavel.update({end_atv_key: end_atv_var_value})

    # Adicionando um número ao nó e progredindo
    mapa_atividades = {atividade: i + 2 for i, atividade in enumerate(atividades_pert.keys())}
    mapa_atividades["inicio"] = 1

    # Criação da lista que vai receber os dados no formato convertido
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

    # Construir o grafo
    grafo = defaultdict(list)
    for atividade in atividades_convertidas:
        no_inicial = atividade["no_inicial"]
        no_final = atividade["no_final"]
        grafo[no_inicial].append(no_final)

    # Criar o diagrama
    dot = graphviz.Digraph(comment='Diagrama de Atividades', format='png')
    dot.attr(rankdir='LR')  # Definir o layout como horizontal
    dot.attr('node', shape='rectangle')  # Definir o formato dos nós como retângulos

    # Adicionar nós e arestas ao diagrama
    for atividade, no in mapa_atividades.items():
        # print(no)  # 9, 10, 1
        # print(atividade)  # 8, fim, início
        dot.node(str(no), atividade)

    for no_inicial, nos_finais in grafo.items():
        for no_final in nos_finais:
            dot.edge(str(no_inicial), str(no_final))
    
    # Função para encontrar todos os caminhos usando DFS (Busca em Profundidade)
    def encontrar_caminhos(grafo, inicio, fim, caminho=[]): 
        caminho = caminho + [inicio]
        if inicio == fim:
            return [caminho]
        if inicio not in grafo:
            return []
        caminhos = []
        for no in grafo[inicio]:
            if no not in caminho:  # Evitar ciclos
                novos_caminhos = encontrar_caminhos(grafo, no, fim, caminho)
                for novo_caminho in novos_caminhos:
                    caminhos.append(novo_caminho)
        return caminhos

    # Função para calcular a duração de um caminho
    def calcular_duracao_caminho(caminho, atividades_convertidas, duracoes_atividade, tempos_riscos):  # duracoes_AtividadeS ?
        duracao = 0  # duração do caminho
        custo_total = 0  # custo do caminho
        #print(atividades_convertidas)
        for i in range(len(caminho) - 1):
            no_inicial = caminho[i]
            no_final = caminho[i + 1]
            for atividade in atividades_convertidas:
                if atividade["no_inicial"] == no_inicial and atividade["no_final"] == no_final:
                    if "duracao" in atividade:
                        duracao_atividade = atividade["duracao"]  # duração da atividade
                    else:
                        # Calcular a duração com base no tipo de distribuição
                        tipo = atividade["tipo"]
                        if tipo == "beta_pert":     # errado
                            t_o = atividade["t_otimista"]
                            t_p = atividade["t_pessimista"]
                            t_m = atividade["t_provavel"]

                            # Calculando os parâmetros alpha e beta da distribuição beta
                            alpha = 1 + 4 * (t_m - t_o) / (t_p - t_o)
                            beta = 1 + 4 * (t_p - t_m) / (t_p - t_o)

                            # Gerando uma variável aleatória beta e escalando para o intervalo [t_o, t_p]
                            beta_random = np.random.beta(alpha, beta)
                            duracao_atividade = beta_random * (t_p - t_o) + t_o

                         #   print(f'atv stats for each way activity {atividade.get('no_inicial')} --> {atividade.get('no_final')}')
                          #  print(f'alpha: {alpha}, beta: {beta}, random: {beta_random}')
                          #  print(f'duração: {duracao_atividade}')
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
                    duracoes_atividades[atividade["no_final"] - 2] = duracao_atividade  # Atribui a duração da atividade no índice correto
                    print(f'Atividade {int(atividade["no_final"] -1)}, no {atividade["no_inicial"]}-{atividade["no_final"]}; Duração atv: {duracao_atividade}, Duração caminho: {duracao}')

                    # Custo
                    idx = str(atividade.get("no_inicial"))  # não inclui risco ainda
                    custo_fix = custo_fixo.get(idx)
                    custo_var = custo_variavel.get(idx) * duracao_atividade
                    custo = custo_fix + custo_var
                    custo_total += custo

        # Verificar se os riscos ocorreram nesta iteração
        for risco, detalhes in riscos.items():
            ocorreu = random.random() < detalhes["probabilidade"]
            print(f'{ocorreu}')
            riscos_ocorridos[risco].append(ocorreu)
            if ocorreu:
                atraso_total = 0  # tempo de atraso da atividade
                for atividade in detalhes["atividades_afetadas"]:
                    if int(atividade) + 1 in caminho:
                        print(f'atividade: {atividade}')
                        index_atividade = mapa_atividades[atividade] - 2
                        print(f'staticiscs: idx: {index_atividade} at {mapa_atividades}')
                        if detalhes["tipo_dist"] == "triangular":
                            atraso = np.random.triangular(detalhes["atraso_minimo"], detalhes["atraso_medio"], detalhes["atraso_maximo"])
                        elif detalhes["tipo_dist"] == "uniforme":   
                            atraso = np.random.uniform(detalhes["atraso_minimo"], detalhes["atraso_maximo"])
                            print('delay:')
                            print(atraso)

                        if detalhes["tipo"] == "absoluto":  # Tipo do risco é absoluto
                            duracoes_atividades[index_atividade] += atraso
                        else:  # Tipo do risco é percentual
                            print('duracao antes atraso :')
                            print(duracoes_atividades[index_atividade])
                            duracoes_atividades[index_atividade] *= (1 + atraso)  # erro?
                            atraso = duracoes_atividades[index_atividade] * atraso
                            print('duracao após risco:')
                            print(duracoes_atividades[index_atividade])
                            print(f'novo atraso: {atraso}.')


                        atraso_total += atraso
                tempos_riscos[risco].append(atraso_total)
            else:
                tempos_riscos[risco].append(0)  
            duracao_risco = {risco: sum(valores) for risco, valores in tempos_riscos.items()}

            break

        print(f'duracoes : {duracao}, c risco: {duracao_risco}')
        duracao += sum(duracao_risco.values()) # adicionar o valor de cada risco à duração

        return duracao, duracao_risco, custo_total

    # Solicitar o número de interações para a simulação de Monte Carlo
    # num_iteracoes = int(input("Digite o número de interações para a simulação de Monte Carlo: "))
    # num_iteracoes = 1000
    # Encontrar e reunir em uma lista os caminhos
    caminhos = encontrar_caminhos(grafo, mapa_atividades["inicio"], mapa_atividades['fim'])

    # Inicializar contadores para os caminhos críticos e atividades críticas
    contagem_caminhos_criticos = {tuple(caminho): 0 for caminho in caminhos}  ## converter aqui?

    contagem_atividades_criticas = {atividade: 0 for atividade in atividades_pert.keys()}

    # Realizar a simulação de Monte Carlo
    resultados_atividades = []  # lista de listas dos valores da duracao de cada iteração   # não bate com caminhos
    resultados_caminhos = []
    resultados_caminhos_criticos = []
    duracoes_projeto = []
    duracoes_risco = {risco: [] for risco in riscos}
    custos_projeto = []

    for iteracao in range(num_iteracoes):
        tempos_riscos = {risco: [] for risco in riscos}
        duracoes_atividades = [0] * len(atividades_pert)  # lista dos valores das duracoes da iteracao atual
        duracoes_caminhos = []
        caminho_critico = None
        duracao_maxima = 0
        duracao_risco_maxima = {risco: 0 for risco in riscos}
        custo_maximo = 0
        print('-------------------------------------------------------------------------')
        print(f'iteração: ' + str(iteracao))
        duracoes_caminho_critico = []

       # print(f'caminhos: ' + str(len(caminhos)) + ', ' + str(caminhos))
        for caminho in caminhos:  # duracao_risco {a:[], b:[]}  --> dict, list //// duracao_risco [1, 2]
            print(f'caminho --> ' + str(caminho))
           # duracao, duracao_risco = calcular_duracao_caminho(caminho, atividades_convertidas, duracoes_atividades, tempos_riscos)
            duracao, duracao_risco, custo_total = calcular_duracao_caminho(caminho, atividades_convertidas, duracoes_atividades, tempos_riscos)
            duracoes_caminhos.append(duracao)
            if duracao > duracao_maxima:
                duracao_maxima = duracao
                caminho_critico = caminho
                duracoes_caminho_critico = duracoes_atividades.copy()  # salva valores do caminho critico
          #  print('caminho da duracao (critico)')
          #  print(caminho_critico)  # printará o caminho crítico da iteração até que haja valor superior, e assim, um novo caminho crítico
            for risco in duracao_risco:
                if duracao_risco[risco] > duracao_risco_maxima[risco]:
                    duracao_risco_maxima[risco] = duracao_risco[risco]

            if custo_total > custo_maximo: # riscos não inclusos no cálculo 
                custo_maximo = custo_total

        
        for risco in riscos:
            duracoes_risco[risco].append(duracao_risco_maxima[risco])  

        if iteracao != 0:  # primeira iteração relativamente ok
            for i in duracoes_caminho_critico:
                if i + 2 in caminho_critico:
                    duracoes_caminho_critico[i] = duracoes_caminho_critico[i]

        resultados_atividades.append(duracoes_caminho_critico)  
        print('result atv')
        print(resultados_atividades)
        #print('res atv 2 e 3: ')
        #print(resultados_atividades[iteracao][1])
        #print(resultados_atividades[iteracao][2])
        resultados_caminhos.append(duracoes_caminhos)
        resultados_caminhos_criticos.append({   # df que não bate com atividades
            "Caminho Crítico": caminho_critico,
            "Número do caminho": f'Caminho {caminhos.index(caminho_critico) + 1}',
            "Duração Crítica": duracao_maxima
        })
        duracoes_projeto.append(duracao_maxima)
        custos_projeto.append(custo_maximo)  # riscos não inclusos
        print('resultados critic:')
        print(resultados_caminhos_criticos)
        # Atualizar contadores
        contagem_caminhos_criticos[tuple(caminho_critico)] += 1
        for no in caminho_critico:
            if no != 1:  # Ignorar o nó inicial
                atividade = list(mapa_atividades.keys())[list(mapa_atividades.values()).index(no)]
                contagem_atividades_criticas[atividade] += 1

    # Calcular frequências
    frequencia_caminhos_criticos = {caminho: contagem / num_iteracoes for caminho, contagem in contagem_caminhos_criticos.items()}
    # Correção da visualização dos nós baseado no índice
    contagem_caminhos_criticos_originais = contagem_caminhos_criticos
    frequencia_caminhos_criticos_originais = frequencia_caminhos_criticos

    contagem_caminhos_criticos = { 
        ('start',) + tuple(item - 1 if isinstance(item, int) else item for item in key[1:-1]) + ('end',): value
        for key, value in contagem_caminhos_criticos.items()
    } 
    frequencia_caminhos_criticos = { 
        ('start',) + tuple(item - 1 if isinstance(item, int) else item for item in key[1:-1]) + ('end',): value
        for key, value in frequencia_caminhos_criticos.items()
    } 

    frequencia_atividades_criticas = {atividade: contagem / num_iteracoes for atividade, contagem in contagem_atividades_criticas.items()}

    # Calcular a crucialidade das atividades usando correlação
    crucialidade_atividades = {}
    for i, atividade in enumerate(atividades_pert.keys()):
        duracoes_atividade = [duracao[i] for duracao in resultados_atividades]

        if np.std(duracoes_atividade) == 0 or np.std(duracoes_projeto) == 0:
            crucialidade_atividades[atividade] = 0
        else:
            correlacao = np.corrcoef(duracoes_atividade, duracoes_projeto)[0, 1]
            crucialidade_atividades[atividade] = correlacao

    print(crucialidade_atividades)

    # Exibir os resultados das simulações
    # print("Durações dos projetos:", duracoes_projeto)
    # print("Caminhos críticos e frequências:", frequencia_caminhos_criticos)
    # print("Atividades críticas e frequências:", frequencia_atividades_criticas)
    # print("Crucialidade das atividades:", crucialidade_atividades)

    # ATIVIDADE NA SETA
    def is_critical(atividade, atividades_criticas):
        frequencia_critica = atividades_criticas.get(atividade)
        if frequencia_critica > 0:
            return 'y'
        else:
            return 'n'
    
    with open('diagramDataset.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ActivityId", "Predecessors", "Crucial"])  # colunas
        
        for atv, pred in precedentes_atividades.items():  # escrever linhas
            pred_str = " ".join(pred)  # Convert list to space-separated string
            critico = is_critical(atv, frequencia_atividades_criticas) 
            if atv == 'fim':
                writer.writerow([int(len(precedentes_atividades)), pred_str, critico])
            else:
                writer.writerow([atv, pred_str, critico])

    encontrar_caminhos_seta('./diagramDataset.csv', './resultadosMontecarlo/diagrama_na_seta')


    ####    GRÁFICOS    ####

    def plotar_distribuicao_atividades(resultados_atividades, atividades_pert):
        for i, atividade in enumerate(atividades_pert.keys()):
            if atividade != "fim":  # Ignorar a atividade de fim
                duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
                plt.figure(figsize=(5,3))
                plt.hist(duracoes_atividade, bins=30, alpha=0.75)
                plt.title(f'Distribuição de Duração - {atividade}', fontsize=10)
                plt.xlabel('Duração', fontsize=8)
                plt.ylabel('Frequência', fontsize=8)
                plt.xticks(fontsize=7) 
                plt.yticks(fontsize=7)
                plt.grid(True)
                # Salvando a imagem para cada atividade
                plt.savefig(f'resultadosMontecarlo/distribuicao_atividade_{atividade}.png')
                plt.close()

    crucialidade_caminhos = {}
    for i, caminho in enumerate(caminhos):
        duracoes_caminho = [duracao[i] for duracao in resultados_caminhos]
        if np.std(duracoes_caminho) == 0 or np.std(duracoes_projeto) == 0:
            crucialidade_caminhos[tuple(caminho)] = 0
        else:
            correlacao = np.corrcoef(duracoes_caminho, duracoes_projeto)[0, 1]
            crucialidade_caminhos[tuple(caminho)] = correlacao
    
    crucialidade_caminhos = { ('start',) + tuple(n - 1 for n in caminho[1:-1]) + ('end',): valor for caminho, valor in crucialidade_caminhos.items() }  # correção da visualização dos nós baseado no índice
    for item in resultados_caminhos_criticos:   
        item["Caminho Crítico"] = ['start', *[x - 1 for x in item["Caminho Crítico"][1:-1]], 'end']

    # Converter os resultados em dataframes para facilitar a exportação
    df_atividades = pd.DataFrame(resultados_atividades, columns=list(atividades_pert.keys()))
    df_caminhos = pd.DataFrame(resultados_caminhos, columns=[f"Caminho {i+1}" for i in range(len(caminhos))])
    df_criticos = pd.DataFrame(resultados_caminhos_criticos)
    df_riscos_ocorridos = pd.DataFrame(riscos_ocorridos)

    df_contagem_caminhos_criticos = pd.DataFrame(list(contagem_caminhos_criticos.items()), columns=["Caminho", "Contagem Crítica"])
    df_frequencia_caminhos_criticos = pd.DataFrame(list(frequencia_caminhos_criticos.items()), columns=["Caminho", "Frequência Crítica"])
    df_contagem_caminhos_criticos_originais = pd.DataFrame(list(contagem_caminhos_criticos_originais.items()), columns=["Caminho", "Contagem Crítica"])
    df_frequencia_caminhos_criticos_originais = pd.DataFrame(list(frequencia_caminhos_criticos_originais.items()), columns=["Caminho", "Frequência Crítica"])


    df_caminhos_criticos = pd.merge(df_contagem_caminhos_criticos, df_frequencia_caminhos_criticos, on="Caminho")
    df_caminhos_criticos_originais = pd.merge(df_contagem_caminhos_criticos_originais, df_frequencia_caminhos_criticos_originais, on="Caminho")
    df_caminhos_criticos_originais.insert(0, "Número do Caminho", range(len(df_contagem_caminhos_criticos_originais)))

    df_contagem_atividades_criticas = pd.DataFrame(list(contagem_atividades_criticas.items()), columns=["Atividade", "Contagem Crítica"])
    df_frequencia_atividades_criticas = pd.DataFrame(list(frequencia_atividades_criticas.items()), columns=["Atividade", "Frequência Crítica"])
    df_merged = df_contagem_atividades_criticas.merge(df_frequencia_atividades_criticas, on="Atividade", how="outer")

    df_crucialidade_atividades = pd.DataFrame(list(crucialidade_atividades.items()), columns=["Atividade", "Crucialidade"])
    df_crucialidade_caminhos = pd.DataFrame(list(crucialidade_caminhos.items()), columns=["Caminho", "Crucialidade"])

    df_duracoes_projeto = pd.DataFrame(duracoes_projeto, columns=["Duração do Projeto"])
    df_duracoes_riscos = pd.DataFrame(duracoes_risco)

    # Criando a planilha
    planilha_path = 'Modelo_Riscos.xlsx'
    with pd.ExcelWriter(planilha_path, engine="openpyxl") as writer:
        # Unir "Tempos de Atividades", "Tempos de Caminhos" e "Caminhos Críticos" em uma única página com duas colunas em branco separando
        df_atividades.to_excel(writer, sheet_name='Atividades', startrow=0, startcol=0, index_label="Iteração")
        df_caminhos.to_excel(writer, sheet_name='Caminhos por Iteração', startrow=0, startcol=0, index_label="Iteração")
        df_criticos.to_excel(writer, sheet_name='Caminhos Críticos por Iteração', startrow=0, startcol=0, index_label="Iteração")   # não bate com "Atividadades"
        df_riscos_ocorridos.to_excel(writer, sheet_name='Riscos', index=False)
        # Unir "Contagem Caminhos Críticos", "Frequência Caminhos Críticos", "Contagem Atividades Críticas", "Frequência Atividades Críticas", "Crucialidade das Atividades" e "Crucialidade dos Caminhos" em outra página
        df_caminhos_criticos.to_excel(writer, sheet_name='Caminhos Críticos', startrow=0, index_label="Número do Caminho")

        df_merged.to_excel(writer, sheet_name='Atividades Críticas', index=False)

        df_crucialidade_atividades.to_excel(writer, sheet_name='Crucialidade Atividades', startrow=0, index=False)

        # Salva df_crucialidade_caminhos ao lado do primeiro DataFrame
        df_crucialidade_caminhos.to_excel(writer, sheet_name='Crucialidade Caminhos', startrow=0, startcol=0, index=False)

        # Adicionar os dados de risco à planilha
        df_duracoes_projeto.to_excel(writer, sheet_name='Distribuição Projeto e Risco', startcol=0, index=False)

        writer.book.save(planilha_path)

    def criar_diagrama_atualizado(caminhos_df):
        dot = graphviz.Digraph(comment='Diagrama de Atividades Atualizado', format='png')
        dot.attr(rankdir='LR')  # Layout horizontal
        dot.attr('node', shape='rectangle')  # Formato dos nós

        # Adicionar nós ao diagrama
        for atividade, no in mapa_atividades.items():
            dot.node(str(no), atividade)

        arestas = {}   # Dicionário para rastrear arestas com suas cores

        for _, row in caminhos_df.iterrows():
            caminho = row['Caminho']
            frequencia = row['Frequência Crítica']
            
            if isinstance(caminho, str):   # Certificar-se de que 'caminho' é uma sequência de elementos
                caminho = tuple(map(int, caminho.strip("()").split(", ")))

            cor = 'red' if frequencia > 0.1 else 'black' 
            
            for j in range(len(caminho) - 1):
                aresta = (str(caminho[j]), str(caminho[j + 1]))
                if aresta in arestas:  # Se a aresta for crítica (vermelha), sobrescrever as outras
                    if cor == 'red':
                        arestas[aresta] = cor
                else:
                    arestas[aresta] = cor

        for (inicio, fim), cor in arestas.items():
            dot.edge(inicio, fim, color=cor, penwidth='2.0')

        dot.render('resultadosMontecarlo/diagrama_atividades_atualizado')

    # Chamar a função após a criação da planilha
    criar_diagrama_atualizado(df_caminhos_criticos_originais)

    # Gerar gráficos de caminhos
    for i, caminho in enumerate(caminhos):

        duracoes_caminho = [resultado[i] for resultado in resultados_caminhos]

        plt.figure(figsize=(5, 3))
        plt.hist(duracoes_caminho, bins=30, alpha=0.75, color='blue', edgecolor='black')
        plt.xlabel('Duração', fontsize=8)
        plt.ylabel('Frequência', fontsize=8)

        caminho_update =  [x - 1 for x in caminho[1:-1]]
        plt.title(f'Distribuição das Durações do Caminho {i} : {caminho_update} - Simulação de Monte Carlo', fontsize=10)
        plt.xticks(fontsize=7) 
        plt.yticks(fontsize=7)
        plt.grid(True)
        plt.savefig(f'resultadosMontecarlo/distribuicao_caminho_{i}.png')
        plt.close()

    # Plotar a distribuição das durações do projeto
    plt.figure(figsize=(5, 3))
    plt.hist(df_duracoes_projeto["Duração do Projeto"], bins=30, alpha=0.75, color='blue', edgecolor='black')
    plt.xlabel('Duração do Projeto', fontsize=8)
    plt.ylabel('Frequência', fontsize=8)
    plt.title('Distribuição dos Caminhos Críticos - Simulação de Monte Carlo', fontsize=10)
    plt.xticks(fontsize=7) 
    plt.yticks(fontsize=7)
    plt.grid(True)
    plt.savefig('resultadosMontecarlo/distribuicao_duracao_projeto.png')
    plt.close()

    # Coletar a média dos tempos pela planilha

    # Função para calcular as médias dos tempos das atividades
    def calcular_medias_atividades(resultados_atividades):
        medias = {}
        for i, atividade in enumerate(atividades_pert.keys()):
            duracoes = [resultado[i] for resultado in resultados_atividades]
            medias[atividade] = np.mean(duracoes)

        return medias

    # Função para determinar os tempos de início e término
    def calcular_tempos_atividades(medias, precedentes_atividades):
        tempos_inicio = {}
        tempos_termino = {}
        
        for atividade, precedentes in precedentes_atividades.items():
            if not precedentes:
                tempos_inicio[atividade] = 0
            else:
                tempos_inicio[atividade] = max(tempos_termino[p] for p in precedentes)
            tempos_termino[atividade] = tempos_inicio[atividade] + medias[atividade]
        
        return tempos_inicio, tempos_termino

    # Calcular as médias dos tempos das atividades
    medias = calcular_medias_atividades(resultados_atividades)

    # Determinar os tempos de início e término das atividades
    tempos_inicio, tempos_termino = calcular_tempos_atividades(medias, precedentes_atividades)

    # Plotar o gráfico de Gantt
    def plotar_grafico_gantt(tempos_inicio, tempos_termino):
        fig, ax = plt.subplots(figsize=(8, 4))

        # Definir cores para as barras
        cores = plt.cm.tab10(np.linspace(0, 1, len(tempos_inicio)))

        # Inverter a ordem das atividades
        atividades = list(tempos_inicio.keys())
        atividades.reverse()

        # Criar barras para cada atividade
        entre_barras = 0.1
        for i, atividade in enumerate(atividades):
            inicio = tempos_inicio[atividade]
            termino = tempos_termino[atividade]
            duracao = termino - inicio
            espaco_x = duracao * entre_barras  # Calcular o espaço no eixo x
            ax.barh(atividade, duracao - espaco_x, left=inicio + espaco_x, color=cores[i % len(cores)])

        # Posição do início e fim alinhada com as atividades
        primeira_atividade = atividades[-1]  # Primeira atividade no eixo y
        ultima_atividade = atividades[0]    # Última atividade no eixo y

        # Adicionar losango no início
        ax.scatter(0, atividades.index(primeira_atividade), marker='D', color='green', s=100, label="Início")

        # Adicionar losango no fim (atividade fim)
        tempo_final = max(tempos_termino.values())  
        ax.scatter(tempo_final + 1, atividades.index(ultima_atividade), marker='D', color='red', s=100, label="Fim")

        # Ajustar os limites do eixo x
        x_min = 0  # Alinhar 0 ao início do eixo x
        x_max = tempo_final + 1  # Adicionar espaço no final para o marcador "Fim"
        ax.set_xlim(x_min, x_max)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, linestyle='--', color='gray')

        # Adicionar tempos finais ao eixo x
        for atividade, termino in tempos_termino.items():
            ax.text(termino, atividade, f'{termino:.2f}', va='center', ha='left')

        # Adicionar setas baseadas nas precedências
        for atividade, predecessoras in precedentes_atividades.items():
            for predecessora in predecessoras:
                x_start = tempos_termino[predecessora]  # Termino da predecessora
                y_start = atividades.index(predecessora)  # Índice da predecessora no eixo y
                x_end = tempos_inicio[atividade] + ((tempos_termino[atividade] - tempos_inicio[atividade]) * entre_barras)  # Início da atividade atual
                y_end = atividades.index(atividade)  # Índice da atividade atual no eixo y

                # Desenhar a seta
                cor_seta = cores[atividades.index(atividade) % len(cores)]  # Cor da barra da atividade destino
                ax.annotate(
                    '',
                    xy=(x_end, y_end),
                    xytext=(x_start, y_start),
                    arrowprops=dict(
                        facecolor=cor_seta,
                        edgecolor=cor_seta,
                        arrowstyle='->',
                        mutation_scale=10,         # Escala do tamanho da seta
                        lw=1.25,
                        linestyle='dotted',  # Linha pontilhada
                        connectionstyle="angle",  # Curva angular
                    )
                )

        ax.set_xlabel('Tempo')
        ax.set_ylabel('Atividades')
        ax.set_title('Gráfico de Gantt - Projeto')
        plt.grid(True)
        plt.savefig('resultadosMontecarlo/grafico_gantt.png')
        plt.close()
        
        return fig

    # Cálculo das médias
    medias = calcular_medias_atividades(resultados_atividades)

    # Cálculo dos tempos de início e término
    tempos_inicio, tempos_termino = calcular_tempos_atividades(medias, precedentes_atividades)

    def plotar_grafico_tornado():
        # Calcular impacto percentual
        impactos_atividades = {}
        for i, atividade in enumerate(atividades_pert.keys()):
            duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
            correlacao = np.corrcoef(duracoes_atividade, duracoes_projeto)[0, 1]
            impactos_atividades[atividade] = correlacao # * np.std(duracoes_atividade)

        impactos_ordenados = dict(sorted(impactos_atividades.items(), key=lambda item: abs(item[1]), reverse=True))
        atividades = list(impactos_ordenados.keys())
        impactos = list(impactos_ordenados.values())
        atividades.pop()
        impactos.pop()

        # Gerar gfráfico
        plt.figure(figsize=(5, 3))
        atv_bars = plt.barh(atividades, impactos, color='cyan', alpha=0.7)
        # Inserindo os percentuais
        for b, i in zip(atv_bars, impactos):
            if i >= 0:
                plt.text(
                    b.get_width() + 0.005,
                    b.get_y() + b.get_height() / 2,
                    f'{i:.3f}%',
                    va='center',
                    fontsize=9.5,
                    color='black'
                )
            if i < 0:
                plt.text(
                    b.get_width() + 0.005,
                    b.get_y() + b.get_height() / 2,
                    f'{i:.3f}%',
                    va='center',
                    fontsize=9.5,
                    color='black'
                )

        plt.xlabel('Impacto na Duração do Projeto', fontsize=8)
        plt.ylabel('Atividade', fontsize=8)
        plt.title('Gráfico de Tornado - Impacto das Atividades na Duração do Projeto', fontsize=10)
        plt.xticks(fontsize=7) 
        plt.yticks(fontsize=7)
        plt.grid(True)
        plt.savefig('resultadosMontecarlo/grafico_tornado.png')

    def plotar_grafico_tornado_riscos():
        # Calcular impacto percentual
        impactos_atividades = {}
        for i, atividade in enumerate(atividades_pert.keys()):
            duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
            correlacao = np.corrcoef(duracoes_atividade, duracoes_projeto)[0, 1]
            impactos_atividades[atividade] = correlacao # * np.std(duracoes_atividade)  normalize??

        impactos_riscos = {}
        for r in duracoes_risco:
            correlacao_risco = np.corrcoef(duracoes_risco[r], duracoes_projeto)[0, 1]
            impactos_riscos[r] = correlacao_risco

        impactos_ordenados = dict(sorted(impactos_atividades.items(), key=lambda item: abs(item[1]), reverse=True))
        atividades = list(impactos_ordenados.keys())
        impactos_atv = list(impactos_ordenados.values())
        impactos_atv.pop()
        atividades.pop()

        impactos_riscos_ordenados = dict(sorted(impactos_riscos.items(), key=lambda item: abs(item[1]), reverse=True))
        riscos = list(impactos_riscos_ordenados.keys())
        impactos_risk = list(impactos_riscos_ordenados.values())

        # Gerar gfráfico
        plt.figure(figsize=(5, 3))
        atv_bars = plt.barh(atividades, impactos_atv, color='blue', alpha=0.7, label='Atividade')
        risk_bars = plt.barh(riscos, impactos_risk, color='red', alpha=0.7, label='Risco')

        # Inserindo os percentuais
        deslocamento_texto = 0.1  # Ajuste para evitar sobreposição
        for b, i in zip(atv_bars, impactos_atv):
            plt.text(
                b.get_width() + 0.005 if i > 0 else b.get_width() - 0.1,
                b.get_y() + b.get_height() / 2 - deslocamento_texto,  # Deslocamento para cima
                f'{i:.3f}%',
                va='center',
                fontsize=9.5,
                color='black'
            )

        for r, i in zip(risk_bars, impactos_risk):
            plt.text(
                r.get_width() + 0.005 if i > 0 else r.get_width() - 0.1,
                r.get_y() + r.get_height() / 2 + deslocamento_texto,  # Deslocamento para baixo
                f'{i:.3f}%',
                va='center',
                fontsize=9.5,
                color='black'
            )

        
        plt.xlabel('Impacto na Duração do Projeto', fontsize=8)
        plt.ylabel('Atividade/Risco', fontsize=8)
        plt.title('Gráfico de Tornado - Duração do Projeto e Riscos por Atividade', fontsize=10)
        plt.xticks(fontsize=7) 
        plt.yticks(fontsize=7)
        plt.legend(loc='upper right', fontsize=6.5)
        plt.grid(True)
        plt.savefig('resultadosMontecarlo/grafico_tornado_riscos.png')

    # Carrega a planilha que contém os dados
    file_path = 'Modelo_Riscos.xlsx'

    # Lê apenas as duas primeiras colunas: 'Atividade' e 'Contagem Crítica'
    df = pd.read_excel(file_path, sheet_name='Atividades Críticas', usecols=[0, 1])

    # Renomeia as colunas para garantir consistência, se necessário
    df.columns = ['Atividade', 'Contagem Crítica']

    # Remove linhas com valores vazios, se houver
    df.dropna(subset=['Atividade', 'Contagem Crítica'], inplace=True)

    # Certifica-se de que a 'Contagem Crítica' está no formato correto (numérico)
    df['Contagem Crítica'] = pd.to_numeric(df['Contagem Crítica'], errors='coerce')

    # Remove linhas onde a contagem crítica não é válida
    df.dropna(subset=['Contagem Crítica'], inplace=True)

    # A partir daqui, pode-se continuar com a lógica de cálculo de crucialidade e criticidade
    # Por exemplo, calcular a crucialidade:
    df['Criticidade'] = df['Contagem Crítica'] / df['Contagem Crítica'].max()

    # Exibe as atividades ordenadas pela contagem crítica
    df_sorted = df.sort_values(by='Contagem Crítica', ascending=False)

    df = pd.DataFrame(df_sorted)
    # Removendo a atividade dummy
    df = df[df['Atividade'] != 'fim']

    # Configura o gráfico
    plt.figure(figsize=(5, 3))
    plt.bar(df['Atividade'], df['Criticidade'], color='skyblue')
    plt.xlabel('Atividade', fontsize=8)
    plt.ylabel('Criticidade', fontsize=8)
    plt.title('Gráfico da Criticidade das Atividades', fontsize=10)
    plt.xticks(ticks=range(len(df['Atividade'])), labels=df['Atividade'], fontsize=7)  
    plt.yticks(fontsize=7)
    plt.xticks(df['Atividade'])  # Define os ticks do eixo x para mostrar todas as atividades

    # Exibe o gráfico
    plt.savefig('resultadosMontecarlo/grafico_criticidade.png')

    def plotar_grafico_criticidade(df_frequencia_atividades_criticas):
        plt.figure(figsize=(5, 3))

        df = df_frequencia_atividades_criticas[df_frequencia_atividades_criticas['Atividade'] != 'fim']  # remove atividade fim do dataframe

        # Ordenar os dados pela frequência
        df = df.sort_values(by="Frequência Crítica", ascending=False)

        # Plotar o gráfico de barras
        plt.bar(df["Atividade"], df["Frequência Crítica"], color='skyblue')

        # Adicionar títulos e labels
        plt.xlabel('Atividade', fontsize=8)
        plt.ylabel('Frequência Crítica', fontsize=8)
        plt.title('Frequência de Atividades Críticas - Simulação de Monte Carlo', fontsize=10)
        plt.xticks(rotation=0, fontsize=7)  # Rotacionar os rótulos do eixo X para melhor legibilidade
        plt.yticks(fontsize=7)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Salvar o gráfico
        plt.savefig('resultadosMontecarlo/grafico_criticidade_atividades.png')
        plt.close()


    def plotar_crucialidade_atividades(duracoes_projeto, resultados_atividades, atividades_pert):
        for i, atividade in enumerate(atividades_pert.keys()):
            if atividade != "fim":  # Ignorar a atividade de fim
                R = 'Correlação: ' + str(round(crucialidade_atividades.get(atividade), 8))
                duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
                
                plt.figure(figsize=(5, 3))
                plt.scatter(duracoes_projeto, duracoes_atividade, alpha=0.75, s=25)

                # Adicionando uma linha de tendência fina
                coef = np.polyfit(duracoes_projeto, duracoes_atividade, 1)
                poly1d_fn = np.poly1d(coef)
                plt.plot(duracoes_projeto, poly1d_fn(duracoes_projeto), 'r-', linewidth=0.5)  # Linha fina em vermelho

                plt.title(f'Crucialidade - {atividade}', fontsize=10)
                plt.xlabel('Duração Crítica do Projeto', fontsize=8)
                plt.ylabel('Duração da Atividade', fontsize=8)
                plt.xticks(fontsize=7) 
                plt.yticks(fontsize=7)
                plt.grid(True)

                ax_inset = inset_axes(plt.gca(), width="30%", height="30%", loc='lower right') 
                ax_inset.text(0.5, 0.25, R, fontsize=7, va='center', ha='center', 
                            bbox=dict(facecolor='white', alpha=0.8))
                ax_inset.axis('off')  

                plt.tight_layout()

                # Salvando a imagem para cada atividade
                try:
                    plt.savefig(f'resultadosMontecarlo/cruci_atividade_{atividade}.png')
                except Exception as e:
                    print(f"Erro ao salvar a imagem para a atividade {atividade}: {e}")                
                plt.close()
    # Supondo que os dados estão na coluna "Duração do Projeto"
    duracoes_projeto_series = df_duracoes_projeto["Duração do Projeto"]

    # Calcular as estatísticas
    tempo_min = np.min(duracoes_projeto_series)
    tempo_max = np.max(duracoes_projeto_series)
    media = np.mean(duracoes_projeto_series)
#    moda_result = stats.mode(duracoes_projeto_series, keepdims=True)  # Usar keepdims para manter a saída como array
#    moda = moda_result.mode[0] if moda_result.mode.size > 0 else None  # Garantir que existe uma moda
    variancia = np.var(duracoes_projeto_series)
    desvio_padrao = np.std(duracoes_projeto_series)

    # Criar uma string com os valores
    valores_texto = (
        f"Tempo Mínimo: {tempo_min:.2f}\n"
        f"Tempo Máximo: {tempo_max:.2f}\n"
        f"Média: {media:.2f}\n"
    #    f"Moda: {moda:.2f}\n"
        f"Variância: {variancia:.2f}\n"
        f"Desvio Padrão: {desvio_padrao:.2f}"
    )

    def plotar_grafico_distribuicao_acumulada_colunas(duracoes_projeto, valores_texto, bin_size=0.5):
        duracoes_min = np.min(duracoes_projeto)  
        duracoes_max = np.max(duracoes_projeto)
        bins = np.arange(duracoes_min, duracoes_max + bin_size, bin_size)

        hist, bin_edges = np.histogram(duracoes_projeto, bins=bins)
        frequencias_relativas = hist / np.sum(hist)  # Frequência relativa de cada bin
        distribuicao_acumulada = np.cumsum(frequencias_relativas)  # Probabilidade acumulada

        bin_midpoints = bin_edges[:-1] + bin_size / 2  

        plt.figure(figsize=(5, 3))
        plt.step(bin_midpoints, distribuicao_acumulada, where='mid', color='blue', linewidth=1, alpha=0.75)
        plt.title('Gráfico da Distribuição Acumulada - Duração do Projeto', fontsize=10)
        plt.xlabel('Tempo (Duração do Projeto)', fontsize=8)
        plt.ylabel('Probabilidade Acumulada', fontsize=8)  # Alterado para refletir a mudança

        plt.xticks(np.linspace(duracoes_min, duracoes_max, 7), fontsize=7)
        plt.yticks([0.0, 0.25, 0.50, 0.75, 1.00], fontsize=7)  # Ajustado para variar de 0 a 1
        plt.grid(True)

        ax_inset = inset_axes(plt.gca(), width="30%", height="30%", loc='lower right') 
        ax_inset.text(0.5, 0.5, valores_texto, fontsize=7, va='center', ha='center', 
                    bbox=dict(facecolor='white', alpha=0.8))
        ax_inset.axis('off')

        plt.savefig('resultadosMontecarlo/grafico_distribuicao_acumulada_com_estatisticas.png')

    def plotar_grafico_distribuicao_acumulada_riscos(duracao_risco):  # if risco não ocorrer em nenhuma iteração --> erro
        plt.figure(figsize=(5, 3))
        cores = ['red', 'green', 'yellow', 'cyan', 'purple', 'gray', 'brown', 'pink', 'violet']
        duracoes_min_tot = duracao_risco.min().min()
        duracoes_max_tot = duracao_risco.max().max()
        i = 0

        acumulada_total = 0 

        for risco in duracao_risco.columns:
            tempos = duracao_risco[risco].values

            duracoes_min = np.min(tempos)
            duracoes_max = np.max(tempos)
            bin_size = 0.5  # Tamanho do intervalo
            bins = np.arange(duracoes_min, duracoes_max + bin_size, bin_size)
    
            hist, bin_edges = np.histogram(tempos, bins=bins)
            contagem_acumulada = np.cumsum(hist)

            bin_midpoints = bin_edges[:-1] + bin_size / 2
    
            # Plotando o gráfico
            plt.step(bin_midpoints, contagem_acumulada, where='mid', color=cores[i], linewidth=1, alpha=0.85, label=f'Risco {risco}')
            i += 1
    
        # Configurações do gráfico
        plt.title('Gráfico da Distribuição Acumulada - Duração dos Riscos', fontsize=10)
        plt.xlabel('Tempo (Duração do Projeto)', fontsize=8)
        plt.ylabel('Número de Iterações (Acumuladas)', fontsize=8)
        plt.grid(True)
        plt.legend(fontsize=7)
    
        # Ajuste de ticks no eixo x e y
        xticks = np.linspace(duracoes_min_tot, duracoes_max_tot, 7)
        yticks = np.linspace(0, contagem_acumulada[-1], 7)
        plt.xticks(xticks, fontsize=8)
        plt.yticks(yticks, fontsize=8)
            
        plt.savefig(f'resultadosMontecarlo/grafico_distribuicao_acumulada_risco.png')

    def plotar_distribuicao_acumulada_colunas_e_riscos(duracoes_projeto, duracoes_risco):
        plt.figure(figsize=(5, 3))
        bin_size = 0.5  # Tamanho do intervalo
        duracoes_min_tot = min(duracoes_projeto.min(), duracoes_risco.min().min())  # Intervalos agrupados para deixar a distibuição mais granular
        duracoes_max_tot = max(duracoes_projeto.max(), duracoes_risco.max().max())
        bins = np.arange(duracoes_min_tot, duracoes_max_tot + bin_size, bin_size)

        # Projeto
        hist, bin_edges = np.histogram(duracoes_projeto, bins=bins)
        contagem_acumulada = np.cumsum(hist)
        
        bin_midpoints = bin_edges[:-1] + bin_size / 2  # Meio do intervalo é o valor do eixo x

        plt.step(bin_midpoints, contagem_acumulada, where='mid', color='blue', linewidth=1, alpha=0.75, label='Projeto')  # Formato de escada

        # Riscos
        cores = ['red', 'green', 'yellow', 'cyan', 'purple', 'gray', 'brown', 'pink', 'violet']

        i = 0    
        for risco in duracoes_risco.columns:
            tempos = duracoes_risco[risco].values
            hist, bin_edges = np.histogram(tempos, bins=bins)
            contagem_acumulada = np.cumsum(hist)  

            # Plotando o gráfico
            plt.step(bin_midpoints, contagem_acumulada, where='post', color=cores[i], linewidth=1, linestyle=':', alpha=0.85, label=f'Risco {risco}')
            i += 1
    
        # Configurações do gráfico
        plt.title('Gráfico da Distribuição Acumulada - Duração do Projeto e Riscos', fontsize=10)
        plt.xlabel('Tempo (Duração do Projeto)', fontsize=8)
        plt.ylabel('Número de Iterações (Acumuladas)', fontsize=8)
        plt.grid(True)
        plt.legend(fontsize=7)
    
        # Ajuste de ticks no eixo x e y
        xticks = np.linspace(duracoes_min_tot, duracoes_max_tot, 7)
        yticks = np.linspace(0, contagem_acumulada[-1], 7)
        plt.xticks(xticks, fontsize=8)
        plt.yticks(yticks, fontsize=8)
            
        plt.savefig(f'resultadosMontecarlo/grafico_distribuicao_acumulada_projeto_e_riscos.png')

    def plotar_analise_custos(custos, duracoes):
        duracoes.sort()
        custos.sort()

        x, y = np.array(duracoes), np.array(custos)

        X_Y_Spline = make_interp_spline(x, y)
        X_ = np.linspace(x.min(), x.max(), 500)
        Y_ = X_Y_Spline(X_)
        
        plt.figure(figsize=(5, 3))

        plt.plot(x, y, linestyle='-', color='green')
        # Configurações do gráfico
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        plt.title('Análise de Valor Agregado', fontsize=10)
        plt.xlabel('Tempo (Duração do Projeto)', fontsize=8)
        plt.ylabel('Custo Total do Projeto', fontsize=8)
        plt.grid(True)
        plt.legend(fontsize=7)

        plt.savefig(f'resultadosMontecarlo/grafico_analise_custos.png')

    # Plotar gráficos
    plotar_distribuicao_atividades(resultados_atividades, atividades_pert)
    criar_diagrama_atualizado(df_caminhos_criticos_originais)
    plotar_grafico_gantt(tempos_inicio, tempos_termino)
    plotar_crucialidade_atividades(df_duracoes_projeto["Duração do Projeto"], resultados_atividades, atividades_pert)
    plotar_grafico_tornado()
    plotar_grafico_criticidade(df_frequencia_atividades_criticas)
    dot.render('resultadosMontecarlo/diagrama_atividades', format='png', cleanup=True)

    if num_iteracoes > 3:  # isola gráficos que necessitam de um valor mínimo para plotar corretamente 
        plotar_analise_custos(custos_projeto, duracoes_projeto)

    if num_iteracoes > 1:
        plotar_grafico_distribuicao_acumulada_colunas(df_duracoes_projeto["Duração do Projeto"], valores_texto)

    if riscos:  # riscos opcionais (dicionário não está vazio)
        plotar_grafico_tornado_riscos()

        if num_iteracoes > 1:
            plotar_grafico_distribuicao_acumulada_riscos(df_duracoes_riscos)
            plotar_distribuicao_acumulada_colunas_e_riscos(df_duracoes_projeto["Duração do Projeto"], df_duracoes_riscos)



    imagem_diagrama = ["diagrama_atividades.png"]
    imagens_atividades = glob.glob("resultadosMontecarlo/distribuicao_atividade_*.png")
    imagens_caminhos = glob.glob("resultadosMontecarlo/distribuicao_caminho_*.png")
    imagem_projeto = ["distribuicao_duracao_projeto.png"]
    imagem_gantt = ["grafico_gantt.png"]
    imagem_tornado = ["grafico_tornado.png"]
    imagem_tornado_riscos = ["grafico_tornado_riscos.png"]
    imagens_atv_crucialidade = glob.glob("resultadosMontecarlo/cruci_atividade_*.png")
    imagem_seta = ["./resultadosMontecarlo/diagrama_na_seta.png"]
    
    # Retorne todas as imagens geradas
    return imagem_diagrama + imagens_atividades + imagens_caminhos + imagem_projeto + imagem_gantt + imagem_tornado + imagem_tornado_riscos + imagens_atv_crucialidade + imagem_seta + [planilha_path]

