import random
import numpy as np
import graphviz
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import glob


def simular_montecarlo(atividades_pert, riscos, num_interacoes):

    precedentes_atividades = {atividade: detalhes["precedentes"] for atividade, detalhes in atividades_pert.items()}

    riscos_ocorridos = {risco: [] for risco in riscos}
    tempos_riscos = {risco: [] for risco in riscos}


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
                        # Calcular a duração com base no tipo de distribuição
                        tipo = atividade["tipo"]
                        if tipo == "beta_pert":
                            t_o = atividade["t_otimista"]
                            t_p = atividade["t_pessimista"]
                            t_m = atividade["t_provavel"]

                            # Calculando os parâmetros alpha e beta da distribuição beta
                            alpha = 1 + 4 * (t_m - t_o) / (t_p - t_o)
                            beta = 1 + 4 * (t_p - t_m) / (t_p - t_o)

                            # Gerando uma variável aleatória beta e escalando para o intervalo [t_o, t_p]
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
                    duracoes_atividades[atividade["no_final"] - 2] = duracao_atividade  # Atribui a duração da atividade no índice correto

                    # Verificar se os riscos ocorreram nesta iteração
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

    # Solicitar o número de interações para a simulação de Monte Carlo
    #num_interacoes = int(input("Digite o número de interações para a simulação de Monte Carlo: "))
    # num_interacoes = 1000
    # Encontrar e reunir em uma lista os caminhos
    caminhos = encontrar_caminhos(grafo, mapa_atividades["inicio"], mapa_atividades['fim'])

    # Inicializar contadores para os caminhos críticos e atividades críticas
    contagem_caminhos_criticos = {tuple(caminho): 0 for caminho in caminhos}
    contagem_atividades_criticas = {atividade: 0 for atividade in atividades_pert.keys()}

    # Realizar a simulação de Monte Carlo
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

        resultados_atividades.append(duracoes_atividades)
        resultados_caminhos.append(duracoes_caminhos)
        resultados_caminhos_criticos.append({
            "Caminho Crítico": caminho_critico,
            "Número do caminho": f'Caminho {caminhos.index(caminho_critico)}',
            "Duração Crítica": duracao_maxima
        })
        duracoes_projeto.append(duracao_maxima)

        # Atualizar contadores
        contagem_caminhos_criticos[tuple(caminho_critico)] += 1
        for no in caminho_critico:
            if no != 1:  # Ignorar o nó inicial
                atividade = list(mapa_atividades.keys())[list(mapa_atividades.values()).index(no)]
                contagem_atividades_criticas[atividade] += 1


    # Calcular frequências
    frequencia_caminhos_criticos = {caminho: contagem / num_interacoes for caminho, contagem in contagem_caminhos_criticos.items()}
    frequencia_atividades_criticas = {atividade: contagem / num_interacoes for atividade, contagem in contagem_atividades_criticas.items()}

    # Calcular a crucialidade das atividades e dos caminhos
    crucialidade_atividades = {}
    for i, atividade in enumerate(atividades_pert.keys()):
        duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
        crucialidade_atividades[atividade] = np.mean(duracoes_atividade)

    # Exibir os resultados das simulações
    # print("Durações dos projetos:", duracoes_projeto)
    # print("Caminhos críticos e frequências:", frequencia_caminhos_criticos)
    # print("Atividades críticas e frequências:", frequencia_atividades_criticas)
    # print("Crucialidade das atividades:", crucialidade_atividades)

    def plotar_distribuicao_atividades(resultados_atividades, atividades_pert):
        for i, atividade in enumerate(atividades_pert.keys()):
            if atividade != "fim":  # Ignorar a atividade de fim
                duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
                plt.figure()
                plt.hist(duracoes_atividade, bins=30, alpha=0.75)
                plt.title(f'Distribuição de Duração - {atividade}')
                plt.xlabel('Duração')
                plt.ylabel('Frequência')
                plt.grid(True)
                # Salvando a imagem para cada atividade
                plt.savefig(f'resultadosMontecarlo/distribuicao_atividade_{atividade}.png')
                plt.close()

    plotar_distribuicao_atividades(resultados_atividades, atividades_pert)

    crucialidade_caminhos = {}
    for i, caminho in enumerate(caminhos):
        duracoes_caminho = [duracao[i] for duracao in resultados_caminhos]
        if np.std(duracoes_caminho) == 0 or np.std(duracoes_projeto) == 0:
            crucialidade_caminhos[tuple(caminho)] = 0
        else:
            correlacao = np.corrcoef(duracoes_caminho, duracoes_projeto)[0, 1]
            crucialidade_caminhos[tuple(caminho)] = correlacao

    # Converter os resultados em dataframes para facilitar a exportação
    df_atividades = pd.DataFrame(resultados_atividades, columns=list(atividades_pert.keys()))
    df_caminhos = pd.DataFrame(resultados_caminhos, columns=[f"Caminho {i+1}" for i in range(len(caminhos))])
    df_criticos = pd.DataFrame(resultados_caminhos_criticos)
    df_riscos_ocorridos = pd.DataFrame(riscos_ocorridos)
    for risco in riscos:
        df_riscos_ocorridos[f"Tempo {risco}"] = tempos_riscos[risco]

    df_contagem_caminhos_criticos = pd.DataFrame(list(contagem_caminhos_criticos.items()), columns=["Caminho", "Contagem Crítica"])
    df_frequencia_caminhos_criticos = pd.DataFrame(list(frequencia_caminhos_criticos.items()), columns=["Caminho", "Frequência Crítica"])
    df_contagem_atividades_criticas = pd.DataFrame(list(contagem_atividades_criticas.items()), columns=["Atividade", "Contagem Crítica"])
    df_frequencia_atividades_criticas = pd.DataFrame(list(frequencia_atividades_criticas.items()), columns=["Atividade", "Frequência Crítica"])
    df_crucialidade_atividades = pd.DataFrame(list(crucialidade_atividades.items()), columns=["Atividade", "Crucialidade"])
    df_crucialidade_caminhos = pd.DataFrame(list(crucialidade_caminhos.items()), columns=["Caminho", "Crucialidade"])
    df_duracoes_projeto = pd.DataFrame(duracoes_projeto, columns=["Duração do Projeto"])

    # Criando a planilha
    planilha_path = 'Modelo_Riscos.xlsx'
    with pd.ExcelWriter(planilha_path) as writer:
        # Unir "Tempos de Atividades", "Tempos de Caminhos" e "Caminhos Críticos" em uma única página com duas colunas em branco separando
        df_atividades.to_excel(writer, sheet_name='Atividades', startrow=0, startcol=0, index_label="Iteração")
        df_caminhos.to_excel(writer, sheet_name='Caminhos', startrow=0, startcol=len(df_atividades.columns) + 2, index_label="Iteração")
        df_criticos.to_excel(writer, sheet_name='Caminhos', startrow=0, startcol=len(df_atividades.columns) + len(df_caminhos.columns) + 4, index_label="Iteração")
        df_riscos_ocorridos.to_excel(writer, sheet_name='Riscos', index=False)

        # Unir "Contagem Caminhos Críticos", "Frequência Caminhos Críticos", "Contagem Atividades Críticas", "Frequência Atividades Críticas", "Crucialidade das Atividades" e "Crucialidade dos Caminhos" em outra página
        df_contagem_caminhos_criticos.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=0, index_label="Caminho")
        df_frequencia_caminhos_criticos.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=len(df_contagem_caminhos_criticos) + 2, index_label="Caminho")
        df_contagem_atividades_criticas.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=len(df_contagem_caminhos_criticos) + len(df_frequencia_caminhos_criticos) + 4, index=False)
        df_frequencia_atividades_criticas.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=len(df_contagem_caminhos_criticos) + len(df_frequencia_caminhos_criticos) + len(df_contagem_atividades_criticas) + 6, index=False)
        df_crucialidade_atividades.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=len(df_contagem_caminhos_criticos) + len(df_frequencia_caminhos_criticos) + len(df_contagem_atividades_criticas) + len(df_frequencia_atividades_criticas) + 8, index=False)
        df_crucialidade_caminhos.to_excel(writer, sheet_name='Caminhos e Atividades Críticas', startrow=len(df_contagem_caminhos_criticos) + len(df_frequencia_caminhos_criticos) + len(df_contagem_atividades_criticas) + len(df_frequencia_atividades_criticas) + len(df_crucialidade_atividades) + 10, index=False)

        # Adicionar os dados de risco à planilha
        df_duracoes_projeto.to_excel(writer, sheet_name='Distribuição Projeto e Risco', index=False)



    # Gerar gráficos de caminhos
    for i, caminho in enumerate(caminhos):
        duracoes_caminho = [resultado[i] for resultado in resultados_caminhos]
        plt.figure(figsize=(10, 6))
        plt.hist(duracoes_caminho, bins=30, alpha=0.75, color='blue', edgecolor='black')
        plt.xlabel('Duração')
        plt.ylabel('Frequência')
        plt.title(f'Distribuição das Durações do Caminho {i} : {caminho} - Simulação de Monte Carlo')
        plt.grid(True)
        plt.savefig(f'resultadosMontecarlo/distribuicao_caminho_{i}.png')
        plt.close()

    # Plotar a distribuição das durações do projeto
    plt.figure(figsize=(10, 6))
    plt.hist(df_duracoes_projeto["Duração do Projeto"], bins=30, alpha=0.75, color='blue', edgecolor='black')
    plt.xlabel('Duração do Projeto')
    plt.ylabel('Frequência')
    plt.title('Distribuição dos Caminhos Críticos - Simulação de Monte Carlo')
    plt.grid(True)
    plt.savefig('resultadosMontecarlo/distribuicao_duracao_projeto.png')
    plt.close()

    # print(precedentes_atividades)
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
        fig, ax = plt.subplots(figsize=(10, 6))

        # Definir cores para as barras
        cores = plt.cm.tab10(np.linspace(0, 1, len(tempos_inicio)))

        # Inverter a ordem das atividades
        atividades = list(tempos_inicio.keys())
        atividades.reverse()

        # Criar barras para cada atividade
        for i, atividade in enumerate(atividades):
            inicio = tempos_inicio[atividade]
            termino = tempos_termino[atividade]
            ax.barh(atividade, termino - inicio, left=inicio, color=cores[i % len(cores)])

        # Adicionar atividade "início" no início (sem duração, apenas um marcador visual)
        ax.barh("Início", 0, left=0, color="green")  # Barra com duração 0 e cor verde

        # Adicionar losango no início (atividade "início")
        ax.scatter(0, len(atividades), marker='D', color='green', s=100, label="Início")  # Posição no eixo y: len(atividades) (acima da primeira atividade)

        # Adicionar losango no fim (última atividade)
        tempo_final = max(tempos_termino.values())  # Tempo final da última atividade
        ax.scatter(tempo_final, -0.5, marker='D', color='red', s=100, label="Fim")  # Posição no eixo y: -0.5 (abaixo da última atividade)

        # Remover linhas horizontais
        ax.yaxis.grid(False)

        # Alterar linhas verticais tracejadas para sólidas
        ax.xaxis.grid(True, linestyle='--', color='gray')

        # Adicionar tempos finais ao eixo x
        for atividade, termino in tempos_termino.items():
            ax.text(termino, atividade, f'{termino:.2f}', va='center', ha='left')

         # Adicionar setas baseadas nas precedências
        for atividade, predecessoras in precedentes_atividades.items():
            for predecessora in predecessoras:
                # Coordenadas para a seta
                x_start = tempos_termino[predecessora]  # Termino da predecessora
                y_start = atividades.index(predecessora)  # Índice da predecessora no eixo y
                x_end = tempos_inicio[atividade]  # Início da atividade atual
                y_end = atividades.index(atividade)  # Índice da atividade atual no eixo y

                # Desenhar a seta
                ax.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start),
                            arrowprops=dict(facecolor='black', arrowstyle='->', lw=1))

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

    fig = plotar_grafico_gantt(tempos_inicio, tempos_termino)

    impactos_atividades = {}
    for i, atividade in enumerate(atividades_pert.keys()):
        duracoes_atividade = [duracao[i] for duracao in resultados_atividades]
        correlacao = np.corrcoef(duracoes_atividade, duracoes_projeto)[0, 1]
        impactos_atividades[atividade] = correlacao * np.std(duracoes_atividade)

    impactos_ordenados = dict(sorted(impactos_atividades.items(), key=lambda item: abs(item[1]), reverse=True))
    atividades = list(impactos_ordenados.keys())
    impactos = list(impactos_ordenados.values())

    plt.figure(figsize=(10, 8))
    plt.barh(atividades, impactos, color='blue', alpha=0.7)
    plt.xlabel('Impacto na Duração do Projeto')
    plt.ylabel('Atividade')
    plt.title('Gráfico de Tornado - Impacto das Atividades na Duração do Projeto')
    plt.grid(True)
    plt.savefig('resultadosMontecarlo/grafico_tornado.png')

    dot.render('resultadosMontecarlo/diagrama_atividades', format='png', cleanup=True)

    # Adicione essa parte ao final da função, para coletar os nomes das imagens geradas:
    imagem_diagrama = ["diagrama_atividades.png"]
    imagens_atividades = glob.glob("resultadosMontecarlo/distribuicao_atividade_*.png")
    imagens_caminhos = glob.glob("resultadosMontecarlo/distribuicao_caminho_*.png")
    imagem_projeto = ["distribuicao_duracao_projeto.png"]
    imagem_gantt = ["grafico_gantt.png"]
    imagem_tornado = ["grafico_tornado.png"]
    
    # Retorne todas as imagens geradas
    return imagem_diagrama + imagens_atividades + imagens_caminhos + imagem_projeto + imagem_gantt + imagem_tornado + [planilha_path]

