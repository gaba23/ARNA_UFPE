import json
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session
from functools import wraps
import os
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment
from openpyxl.drawing.image import Image as XlImage
from graphviz import Digraph
import networkx as nx
import io
import pandas as pd
import csv
from scipy.stats import norm
import numpy as np
import matplotlib.pyplot as plt


app = Flask(__name__, static_folder='static')

''
# Decorator para verificar a autenticação do usuário
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Lógica de verificação da autenticação do usuário
        if not is_user_authenticated():
            # Redirecionar o usuário para a página de login se não estiver autenticado
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_user_authenticated():
    return session.get('authenticated', False)

def authenticate_user():
    session['authenticated'] = True

from flask import session, redirect, url_for

@app.route('/logout')
def logout():
    # Desautentica o usuário
    deauthenticate_user()
    return redirect(url_for('login'))

def deauthenticate_user():
    session.pop('authenticated', None)

def realizar_analise(atividades, Tipo):

    if Tipo == 'PERT':
        def is_edge_in_critical_path(u, v, caminho_critico):
            return (u, v) in zip(caminho_critico[:-1], caminho_critico[1:])
        def is_node_in_critical_path(node, caminho_critico):
            return node in caminho_critico

        # Definir os dados das atividades
        def plot_activities(atividades):
            # Criar o grafo direcionado
            G = nx.DiGraph()

            #Acrescentar T_esperado
            for act in atividades:
                atividades[act]['t_esperado'] = (atividades[act]['t_otimista'] + 4 * atividades[act]['t_provavel'] + atividades[act]['t_pessimista']) / 6

            for act in atividades:
                atividades[act]['dp'] = (atividades[act]['t_pessimista'] - atividades[act]['t_otimista'])/6

            for act in atividades:
                atividades[act]['variance'] = ((atividades[act]['t_pessimista'] - atividades[act]['t_otimista'])/6)**2

            atividades_df = pd.DataFrame.from_dict(atividades, orient='index') 

            # Adicionar os nós e as arestas ao grafo
            for _, info in atividades_df.iterrows():
                duracao = info.get('t_esperado', 0)
                G.add_node(info.name, duracao=duracao)
                precedentes = info.get('precedentes', [])
                for precedente in precedentes:
                    G.add_edge(precedente, info.name, weight=duracao)

            # Adicionar os nós e as arestas ao grafo
            G.add_node("Start", duration=0)  # Nó de início

            for _, info in atividades_df.iterrows():
                duracao = info.get('t_esperado', 0)
                G.add_node(info.name, duracao=duracao)
                precedentes = info.get('precedentes', [])

                # Adicione as arestas entre o nó de início e as atividades iniciais
                if not precedentes:
                    G.add_edge("Start", info.name, weight=duracao)

                for precedente in precedentes:
                    G.add_edge(precedente, info.name, weight=duracao)

            # Encontre as atividades que não são precedentes de outras
            atividades_finais = atividades_df[~atividades_df.index.isin([atividade for info in atividades_df['precedentes'] for atividade in info])]

            # Adicione as arestas das atividades finais ao nó "End"
            for atividade_final in atividades_finais.index:
                G.add_edge(atividade_final, "End", weight=0)

            # Calcular o caminho crítico
            caminho_critico = nx.dag_longest_path(G)

            # Desenhar o grafo usando Graphviz
            dot = Digraph()
            dot.attr(rankdir='LR')  # Configurar o layout da esquerda para a direita
            dot.attr('graph', ranksep='1.5')  # Adicionar o atributo ranksep aqui (aumentar o valor para aumentar o espaço entre os níveis)
            dot.attr('graph', nodesep='0.75')  # Adicionar o atributo nodesep aqui (aumentar o valor para aumentar o espaço entre os nós no mesmo nível)

            # Adicionar os nós e as arestas ao grafo
            for node, data in G.nodes(data=True):
                label = f"{node}"
                dot.node(node, label=label, shape='circle', ports='we')  # Adicionar atributo ports='we' aqui

            edge_number = 1  # Inicializa o contador de numeração das arestas
            edges_df = pd.DataFrame(columns=['Aresta', 'Atividade_Saida', 'Atividade_Chegada'])  # Cria um DataFrame vazio
            for u, v, d in G.edges(data=True):
                edge_label = f'a{edge_number}'  # Nome da aresta
                atividade_saida = u  # Nome do nó de saída da aresta
                atividade_chegada = v  # Nome do nó de chegada da aresta

                edges_df.loc[edge_number - 1] = [edge_label, atividade_saida, atividade_chegada]

                if v == "End" and is_edge_in_critical_path(u, v, caminho_critico):
                    dot.edge(u, v, color='red')
                elif u == caminho_critico[-1] and v == "End":
                    dot.edge(u, v, color='red')
                elif is_edge_in_critical_path(u, v, caminho_critico):
                    dot.edge(u + ":e", v + ":w", color='red')
                else:
                    dot.edge(u + ":e", v + ":w",)

                edge_number += 1

            dot.attr(label='PERT Network', labelloc='bottom')

            # Tempo Total Atividades
            caminho_critico_nos = [node for node in caminho_critico if is_node_in_critical_path(node, caminho_critico)]
            caminho_critico_nos = caminho_critico_nos[1:]

            tempo_total_critico = 0
            for numb in caminho_critico_nos:
                tempo_total_critico += atividades_df.loc [numb, 't_esperado']
            
            caminho_critico_string = " --> ".join(caminho_critico_nos)
            # Salvar a imagem do grafo em formato PNG
            static_dir = os.path.join(os.getcwd(), 'static')
            image_path = os.path.join(static_dir, 'rede_atividades')
            dot.render(image_path, view=False, format='png')
            atividades_df.to_html(static_dir + "/dataframe.html")
            atividades_df.to_excel(static_dir + "/dataframe.xlsx")

            return caminho_critico_string, tempo_total_critico

        caminho_critico, tempo_total = plot_activities(atividades)
        return caminho_critico, tempo_total
            
    elif Tipo == 'CPM':

            def calcular_es_ls(G):
                    # Inicialize dicionários para armazenar os valores de ES e LS
                    es = {}
                    ls = {}

                    # Inicialize todos os ES com zero
                    for node in G.nodes:
                        es[node] = 0

                    # Inicialize todos os LS com um valor grande (infinito)
                    for node in G.nodes:
                        ls[node] = float('inf')

                    # Ordenação topológica do grafo
                    topological_order = list(nx.topological_sort(G))

                    # Calcular o ES
                    for node in topological_order:
                        for predecessor in G.predecessors(node):
                            es[node] = max(es[node], es[predecessor] + G[predecessor][node]['weight'])

                    # Calcular o LS
                    for node in reversed(topological_order):
                        if list(G.successors(node)):  # Verifica se é um nó de término
                            ls[node] = min(ls[succ] - G[node][succ]['weight'] for succ in G.successors(node))
                        else:
                            ls[node] = es[node]

                    return es, ls


            def is_edge_in_critical_path(u, v, caminho_critico):
                return (u, v) in zip(caminho_critico, caminho_critico[1:])

            def plot_activities(atividades):
                # Criar o grafo direcionado
                G = nx.DiGraph()

                atividades_df = pd.DataFrame.from_dict(atividades, orient='index')

                # Adicionar os nós e as arestas ao grafo
                for atividade, info in atividades.items():
                    duracao = info.get('duracao', 0)
                    G.add_node(atividade, duracao=duracao)
                    precedentes = info.get('precedentes', [])
                    for precedente in precedentes:
                        G.add_edge(precedente, atividade, weight=duracao)

                # Calcular o caminho crítico
                caminho_critico = nx.dag_longest_path(G)

                # Calcular Early Start (ES) e Late Start (LS)
                es, ls = calcular_es_ls(G)

                # Calcular Early Finish (ES) e Late Finish (LS)
                ef = {node: es[node] + G.nodes[node]['duracao'] for node in G.nodes()}
                lf = {node: ls[node] + G.nodes[node]['duracao'] for node in G.nodes()}

                # Calcular a folga (float) de cada atividade
                folga = {node: ls[node] - es[node] for node in G.nodes()}

                # Calcular a posição dos nós usando o layout planar com scale=2.0
                pos = nx.planar_layout(G, scale=7.0)

                # Desenhar o grafo usando Graphviz
                dot = Digraph()
                dot.attr(rankdir='LR')  # Configurar o layout da esquerda para a direita
                dot.attr('graph', ranksep='1.5')  # Adicionar o atributo ranksep aqui (aumentar o valor para aumentar o espaço entre os níveis)
                dot.attr('graph', nodesep='0.75')  # Adicionar o atributo nodesep aqui (aumentar o valor para aumentar o espaço entre os nós no mesmo nível)

                # Adicionar os nós e as arestas ao grafo
                for node, data in G.nodes(data=True):
                    label = f"{node} | Peso: {data['duracao']} | ES: {es[node]} / EF: {ef[node]} | LS: {ls[node]} / LF: {lf[node]} | Folga: {folga[node]} "
                    dot.node(node, label=label, shape='record', ports='we')  # Adicionar atributo ports='we' aqui

                initial_nodes = [node for node in G.nodes() if not G.in_edges(node)]
                final_nodes = [node for node in G.nodes() if not G.out_edges(node)]

                dot.node('start', label='start', shape='rectangle')  # Adicionar o nó "start"
                dot.node('end', label='end', shape='rectangle')  # Adicionar o nó "end"

                for initial_node in initial_nodes:
                    dot.edge('start', initial_node + ':w', color='red')  # Conectar "start" aos nós iniciais

                for final_node in final_nodes:
                    dot.edge(final_node + ':e', 'end', color='red')  # Conectar os nós finais ao nó "end"

                label = "Tarefa|Peso|ES e EF|LS e LF|Folga"

                # Criar um subgrafo com o mesmo rank
                with dot.subgraph() as same_rank:
                    same_rank.attr(rank='same')
                    same_rank.node('start')  # Mover o nó "start" para este subgrafo
                    # Adicionar o nó de legenda com atributo "pos" para posicioná-lo abaixo do nó "start"
                    same_rank.node('legend', label=label, shape='record', pos='0,1!', pin='true') 

                for u, v, d in G.edges(data=True):
                    if is_edge_in_critical_path(u, v, caminho_critico):
                        dot.edge(u + ":e", v + ":w", color='red')  # Modificar u para u + ":e" e v para v + ":w" aqui
                    elif v == "end" and is_edge_in_critical_path(u, v, caminho_critico):
                        dot.edge(u, v, color='red')
                    elif u == "start" and is_edge_in_critical_path(u, v, caminho_critico):
                        dot.edge(u, v, color='red')
                    else:
                        dot.edge(u + ":e", v + ":w")  # Modificar u para u + ":e" e v para v + ":w" aqui

                dot.attr(label='CPM Network', labelloc='bottom')

                # Salvar a imagem do grafo em formato PNG
                static_dir = os.path.join(os.getcwd(), 'static')
                image_path = os.path.join(static_dir, 'rede_atividades')
                atividades_df.to_excel(static_dir + "/dataframeCPM.xlsx")
                dot.render(image_path, view=False, format='png')

    if Tipo == 'CPM':
        caminho_critico = plot_activities(atividades)
        return caminho_critico
    elif Tipo == 'PERT':
        caminho_critico, tempo_total, edges_df = plot_activities(atividades)
        return caminho_critico, tempo_total, edges_df

app.secret_key = 'ALDmofmognmg15448d8'
# ------------ ROTAS -----------------

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if is_user_authenticated():
        return redirect(url_for('home'))

    # Lógica de autenticação do usuário
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        if email == 'admin' and senha == '123456':
            # Autenticar o usuário
            authenticate_user() 
            return redirect(url_for('home'))
        else:
            mensagem_erro = 'Usuário ou senha incorretos'
            return render_template('login.html', erro=mensagem_erro)

    return render_template('login.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/PERT')
@login_required
def PERT():
    return render_template('homePERT.html')


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():

        if request.method == 'POST':
            csv_file = request.files['csv_file']  # Obter o arquivo CSV do formulário
            json_file = request.files['json_file']


            if csv_file:  # Se um arquivo CSV foi enviado
                csv_content = csv_file.read().decode('utf-8')

                # Crie uma lista para armazenar os dados do CSV
                atividades_from_csv = {}

                # Use um leitor CSV para ler as linhas do arquivo CSV
                csv_reader = csv.reader(csv_content.splitlines())
                
                # Pule a primeira linha (cabeçalho)
                next(csv_reader)
                
                for row in csv_reader:
                    # Extraia os dados de cada linha
                    atividade, precedentes, ducaracao = row
                    
                    # Converta os valores numéricos para inteiros ou floats, conforme necessário
                    ducaracao = float(ducaracao)
                    
                    # Crie um dicionário para representar cada atividade e seus dados
                    atividade_data = {
                        "precedentes": precedentes.split(', ') if precedentes else [],
                        "ducaracao": ducaracao
                    }
                    
                    # Adicione o dicionário à lista de atividades
                    atividades_from_csv[atividade] = (atividade_data)
                
                atividades_json = atividades_from_csv

            elif json_file:  # Se um arquivo JSON foi enviado
                json_content = json_file.read().decode('utf-8')
                try:
                    data_from_json = json.loads(json_content)
                    atividades_json = data_from_json
                except json.JSONDecodeError:
                    erro = "O arquivo JSON não é válido."
                    return render_template("home.html", erro=erro)
                
            else:
                atividades = request.form.get("atividades")
                # Verificar se o campo de atividades está vazio
                if not atividades:
                    erro = "O campo de atividades não pode estar vazio."
                    return render_template("home.html", erro=erro)
                
                try:
                    atividades_json = json.loads(atividades)

                except json.JSONDecodeError:
                    erro = "O campo de atividades deve ser um JSON válido."
                    return render_template("homePERT.html", erro=erro)

            caminho_critico = realizar_analise(atividades_json, 'CPM')
            session['caminho_critico'] = caminho_critico
            session['atividades_json'] = atividades_json

            return render_template('result.html', caminho_critico=caminho_critico, atividades_json=atividades_json)

"""     if request.method == 'POST':
        csv_file = request.files['csv_file']  # Obter o arquivo CSV do formulário
        if csv_file:  # Se um arquivo CSV foi enviado
            csv_content = csv_file.read().decode('utf-8')
            try:
                atividades_from_csv = json.loads(csv_content)
            except json.JSONDecodeError:
                erro = "O arquivo CSV deve conter um JSON válido."
                return render_template("home.html", erro=erro)
            atividades_json = atividades_from_csv
            
        else:
            atividades = request.form.get("atividades")
            # Verificar se o campo de atividades está vazio
            if not atividades:
                erro = "O campo de atividades não pode estar vazio."
                return render_template("home.html", erro=erro)
            
            try:
                atividades_json = json.loads(atividades)
            except json.JSONDecodeError:
                erro = "O campo de atividades deve ser um JSON válido."
                return render_template("home.html", erro=erro)

        results = realizar_analise(atividades_json, 'CPM')
        session['analysis_results'] = results
        return redirect(url_for('result')) """
    

@app.route('/analyzePERT', methods=['POST'])
@login_required
def analyzePERT():
    if request.method == 'POST':
        csv_file = request.files['csv_file']  # Obter o arquivo CSV do formulário
        json_file = request.files['json_file']


        if csv_file:  # Se um arquivo CSV foi enviado
            csv_content = csv_file.read().decode('utf-8')

            # Crie uma lista para armazenar os dados do CSV
            atividades_from_csv = {}

            # Use um leitor CSV para ler as linhas do arquivo CSV
            csv_reader = csv.reader(csv_content.splitlines())
            
            # Pule a primeira linha (cabeçalho)
            next(csv_reader)
            
            for row in csv_reader:
                # Extraia os dados de cada linha
                atividade, precedentes, t_otimista, t_pessimista, t_provavel = row
                
                # Converta os valores numéricos para inteiros ou floats, conforme necessário
                t_otimista = float(t_otimista)
                t_pessimista = float(t_pessimista)
                t_provavel = float(t_provavel)
                
                # Crie um dicionário para representar cada atividade e seus dados
                atividade_data = {
                    "precedentes": precedentes.split(', ') if precedentes else [],
                    "t_otimista": t_otimista,
                    "t_pessimista": t_pessimista,
                    "t_provavel": t_provavel
                }
                
                # Adicione o dicionário à lista de atividades
                atividades_from_csv[atividade] = (atividade_data)
            
            atividades_json = atividades_from_csv

        elif json_file:  # Se um arquivo JSON foi enviado
            json_content = json_file.read().decode('utf-8')
            try:
                data_from_json = json.loads(json_content)
                atividades_json = data_from_json
            except json.JSONDecodeError:
                erro = "O arquivo JSON não é válido."
                return render_template("home.html", erro=erro)
            
        else:
            atividades = request.form.get("atividades")
            # Verificar se o campo de atividades está vazio
            if not atividades:
                erro = "O campo de atividades não pode estar vazio."
                return render_template("home.html", erro=erro)
            
            try:
                atividades_json = json.loads(atividades)

            except json.JSONDecodeError:
                erro = "O campo de atividades deve ser um JSON válido."
                return render_template("homePERT.html", erro=erro)

        caminho_critico, tempo_total= realizar_analise(atividades_json, 'PERT')
        session['caminho_critico'] = caminho_critico
        session['tempo_total'] = tempo_total
        session['atividades_json'] = atividades_json

        return render_template('resultPERT.html', caminho_critico=caminho_critico, tempo_total=tempo_total)

@app.route('/result')
@login_required
def result():
    return render_template('result.html')


@app.route('/resultPERT')
@login_required
def resultPERT():
    caminho_critico = session.get('caminho_critico')
    tempo_total = session.get('tempo_total')
    edges_df = session.get('edges_df')

    return render_template('resultPERT.html')

@app.route('/download_png')
@login_required
def download_png():
    # Baixar o arquivo PNG do Amazon S3
    """ s3.download_file(BUCKET_NAME, 'rede_atividades.png', 'static/rede_atividades.png') """
    return send_from_directory('static', 'rede_atividades.png', as_attachment=True)

@app.route("/download_pdf_PERT")
@login_required
def download_pdf():
    session.get()
    return send_from_directory('static', 'report_PERT.pdf', as_attachment=True)

@app.route("/download_xls")
@login_required
def download_xls():
    # Baixar o arquivo XLSX do Amazon S3
    """ s3.download_file(BUCKET_NAME, 'report.xlsx', 'static/report.xlsx') """
    return send_from_directory('static', 'dataframe.xlsx', as_attachment=True)

@app.route("/download_xls_CPM")
@login_required
def download_xls_CPM():
    # Baixar o arquivo XLSX do Amazon S3
    """ s3.download_file(BUCKET_NAME, 'report.xlsx', 'static/report.xlsx') """
    return send_from_directory('static', 'dataframeCPM.xlsx', as_attachment=True)


@app.route('/help')
@login_required
def help():
    return render_template('help.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/calculo_tempo', methods=['POST'])
@login_required
def calculo_tempo():
    if request.method == 'POST':
        chegada = request.form.get("chegada")
        saida = request.form.get("saida")
        atividades = session.get('atividades_json')
        caminhos = []
        # Função para encontrar um caminho entre dois nós (entrada e saída)
        def encontrar_caminho(no_atual, saida, caminhos):
            caminhos.append(no_atual)
            if no_atual == saida:
                return True
            elif atividades[no_atual]['precedentes'] == []:
                caminhos = []
                return False
            else:
                for no in atividades[no_atual]['precedentes']:
                   response = encontrar_caminho(no, saida, caminhos)
                   if response == True:
                        return response
            

            caminhos.remove(no_atual)
            return False
        # Verifique se os nós de entrada e saída são válidos

        caminho_bool = encontrar_caminho(chegada, saida, caminhos)

        if caminho_bool == True:
            caminhos = caminhos[::-1]
            soma_result = 0
            for node in caminhos:
                soma_result += atividades[node]['t_esperado']
            string_r = f'PERT NETWORK | CONEXOS | SOMA: {soma_result:.2f}'
        else:
            soma_result = atividades[saida]['t_esperado'] + atividades[chegada]['t_esperado']
            string_r = f'PERT NETWORK | DESCONEXOS | SOMA: {soma_result:.2f}'

        # Criar o grafo direcionado
        G_calculo = nx.DiGraph()

        #Acrescentar T_esperado
        for act in atividades:
            atividades[act]['t_esperado'] = (atividades[act]['t_otimista'] + 4 * atividades[act]['t_provavel'] + atividades[act]['t_pessimista']) / 6

        for act in atividades:
            atividades[act]['dp'] = (atividades[act]['t_pessimista'] - atividades[act]['t_otimista'])/6

        for act in atividades:
            atividades[act]['variance'] = ((atividades[act]['t_pessimista'] - atividades[act]['t_otimista'])/6)**2

        atividades_df = pd.DataFrame.from_dict(atividades, orient='index') 

        # Adicionar os nós e as arestas ao grafo
        for _, info in atividades_df.iterrows():
            duracao = info.get('t_esperado', 0)
            G_calculo.add_node(info.name, duracao=duracao)
            precedentes = info.get('precedentes', [])
            for precedente in precedentes:
                G_calculo.add_edge(precedente, info.name, weight=duracao)

        # Adicionar os nós e as arestas ao grafo
        G_calculo.add_node("Start", duration=0)  # Nó de início

        for _, info in atividades_df.iterrows():
            duracao = info.get('t_esperado', 0)
            G_calculo.add_node(info.name, duracao=duracao)
            precedentes = info.get('precedentes', [])

            # Adicione as arestas entre o nó de início e as atividades iniciais
            if not precedentes:
                G_calculo.add_edge("Start", info.name, weight=duracao)

            for precedente in precedentes:
                G_calculo.add_edge(precedente, info.name, weight=duracao)

        # Encontre as atividades que não são precedentes de outras
        atividades_finais = atividades_df[~atividades_df.index.isin([atividade for info in atividades_df['precedentes'] for atividade in info])]

        # Adicione as arestas das atividades finais ao nó "End"
        for atividade_final in atividades_finais.index:
            G_calculo.add_edge(atividade_final, "End", weight=0)


        # Desenhar o grafo usando Graphviz
        dot = Digraph()
        dot.attr(rankdir='LR')  # Configurar o layout da esquerda para a direita
        dot.attr('graph', ranksep='1.5')  # Adicionar o atributo ranksep aqui (aumentar o valor para aumentar o espaço entre os níveis)
        dot.attr('graph', nodesep='0.75')  # Adicionar o atributo nodesep aqui (aumentar o valor para aumentar o espaço entre os nós no mesmo nível)

        # Adicionar os nós e as arestas ao grafo
        for node, data in G_calculo.nodes(data=True):
            label = f"{node}"
            dot.node(node, label=label, shape='circle', ports='we')  # Adicionar atributo ports='we' aqui

        edge_number = 1  # Inicializa o contador de numeração das arestas
        edges_df = pd.DataFrame(columns=['Aresta', 'Atividade_Saida', 'Atividade_Chegada'])  # Cria um DataFrame vazio
        
        for u, v, d in G_calculo.edges(data=True):
            atividade_saida = u  # Nome do nó de saída da aresta
            atividade_chegada = v  # Nome do nó de chegada da aresta

            if u in caminhos and v in caminhos:
                dot.edge(u, v, color='red')
            else:
                dot.edge(u + ":e", v + ":w",)

        dot.attr(label=f'{string_r}', labelloc='bottom')

        static_dir = os.path.join(os.getcwd(), 'static')
        image_path = os.path.join(static_dir, 'grafo_calculo')
        dot.render(image_path, view=False, format='png')

        return send_from_directory('static', 'grafo_calculo.png', as_attachment=True)

@app.route('/gauss', methods=['POST'])
@login_required
def gauss():
    t_programado = float(request.form.get("t_programado"))
    tempo_total = float(session.get('tempo_total'))
    atividades_json = session.get('atividades_json')

    df = pd.DataFrame.from_dict(atividades_json, orient='index') 

    soma_var = 0

    #df.iterrows() itera sobre cada linha ou index do dataframe
    for index, row in df.iterrows():
        soma_var += row['variance']

    z = (t_programado - tempo_total) / (soma_var**(1/2))
    z = f"{z:.1f}"
    z = float(z)

    mi = tempo_total
    pct_projeto_programado = 50/100

    area = norm.cdf(z)
    print(f"Área: {area:.3f}")

    # Cria um conjunto de valores x no intervalo [tempo_total - 4, tempo_total + 4] para o tempo do projeto
    x = np.linspace(tempo_total - 5, tempo_total + 5, 1000)

    # Calcula a probabilidade acumulada até o valor Z
    area = norm.cdf(z)

    # Cria uma figura e um eixo
    fig, ax = plt.subplots()

    # Plota a curva gaussiana
    ax.plot(x, norm.pdf(x, tempo_total), label='Distribuição Normal')

    # Preenche a área sob a curva até o valor de Z
    ax.fill_between(x, 0, norm.pdf(x, tempo_total), where=(x <= z + tempo_total), alpha=0.3, label=f'Probabilidade = {area:.5f}')

    # Adiciona uma linha vermelha no valor médio (símbolo μ)
    ax.axvline(x=tempo_total, color='red', linestyle='dashed', label=f'Valor Médio (μ = {tempo_total:.2f})')

    # Configurações do gráfico
    ax.set_title('Distribuição Gaussiana com Valor Médio')
    ax.set_xlabel('Tempo Projeto')
    ax.set_ylabel('Densidade de Probabilidade')
    ax.legend()
    static_dir = os.path.join(os.getcwd(), 'static')
    plt.savefig(static_dir + '/grafico_gaussiano.png')
    return send_from_directory('static', 'grafico_gaussiano.png', as_attachment=True)

if __name__ == '__main__':
    app.run()