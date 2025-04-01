from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, JSONResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import csv
import io
import random
import numpy as np
import graphviz
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import glob
from montecarlo import simular_montecarlo
from cpm import calcular_cpm
import os
from pert import calcular_pert
import networkx as nx
import logging
from services.generate_pdf import generate as gerar_pdf


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Obtém o caminho absoluto da pasta onde o executável ou script está rodando
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho absoluto para a pasta 'templates'
templates_dir = os.path.join(base_dir, 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Criação da aplicação FastAPI
app = FastAPI()

# Montando diretórios estáticos com caminhos absolutos
static_dir = os.path.join(base_dir, 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

resultados_montecarlo_dir = os.path.join(base_dir, 'resultadosMontecarlo')
app.mount("/resultadosMontecarlo", StaticFiles(directory=resultados_montecarlo_dir), name="resultadosMontecarlo")

resultados_pert_dir = os.path.join(base_dir, 'resultadosPert')
app.mount("/resultadosPert", StaticFiles(directory=resultados_pert_dir), name="resultadosPert")

resultados_cpm_dir = os.path.join(base_dir, 'resultadosCpm')
app.mount("/resultadosCpm", StaticFiles(directory=resultados_cpm_dir), name="resultadosCpm")

@app.get("/")
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    if email == "admin" and senha == "123456":
        return RedirectResponse(url="/home", status_code=303)
    else:
        erro = "Credenciais inválidas"
        return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

@app.get("/home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/homePERT")
async def home_pert(request: Request):
    return templates.TemplateResponse("homePERT.html", {"request": request})

@app.get("/monteCarlo")
async def home_montecarlo(request: Request):
    return templates.TemplateResponse("monteCarlo.html", {"request": request})

@app.get("/help")
async def help(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.get("/contact")
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    return RedirectResponse(url="/", status_code=303)

@app.post("/analyzeMonteCarlo")
async def analyzeMonteCarlo(request: Request, tabela_atividade: str = Form(None), tabela_risco: str = Form(None), atividades: str = Form(None), riscos: str = Form(None), 
                            csv_file: UploadFile = File(None), xlsx_file: UploadFile = File(None),
                            num_iteracoes: int = Form(...)):  # Adicione o novo parâmetro aqui
  #  logger.info("Analyzing Monte Carlo simulation started.")
    
    if num_iteracoes < 1:
        raise HTTPException(status_code=400, detail="Número de iterações deve ser superior a zero")

    atividades_dict = {}
    riscos_dict = {}
    # Processando arquivos CSV
    if csv_file and csv_file.filename:
        content = await csv_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio")
        
        try:
            content_file = io.StringIO(content.decode('utf-8'))
            df_atv = pd.read_csv(content_file, usecols=range(14))
            content_file.seek(0)  # Resetar ponteiro
            df_riscos = pd.read_csv(content_file, usecols=range(14, 26))

            # Erros de conversão do segundo dataframe
            df_riscos.dropna(how='all', inplace=True)
            df_riscos.rename(columns={'Tipo de Distribuicao.1': 'Tipo de Distribuicao', 'Descricao.1': 'Descricao', 'ID.1': 'ID'}, inplace=True)

            atividades_dict, riscos_dict = parse_mc_csv(df_atv, df_riscos)

        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Arquivo CSV sem dados ou mal formatado")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o CSV: {str(e)}")
        
    # Processando arquivos XLSX
    if xlsx_file and xlsx_file.filename:
        try:
            content = await xlsx_file.read()
            excel_file = io.BytesIO(content)

            sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')  # extrair as páginas
            s_atividades = sheets.get("Atividades")
            s_riscos = sheets.get("Riscos")                

            # Converter em CSV evita formatações ocultas
            csv_buffer_atv = io.StringIO()
            s_atividades.to_csv(csv_buffer_atv, index=False)
            csv_buffer_atv.seek(0)
            # Reconverter em dataframe
            df_atv = pd.read_csv(csv_buffer_atv)

            if s_riscos is not None:  # não é necessário passar a aba dos riscos
                csv_buffer_riscos = io.StringIO()
                s_riscos.to_csv(csv_buffer_riscos, index=False)
                csv_buffer_riscos.seek(0)

                df_riscos = pd.read_csv(csv_buffer_riscos)
            
            else:
                df_riscos = pd.DataFrame()  # dataframe vazio
    
            if df_atv.empty and df_riscos.empty:
                raise HTTPException(status_code=400, detail="Arquivo XLSX vazio ou mal formatado")
            
            atividades_dict, riscos_dict = parse_mc_csv(df_atv, df_riscos)  

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar a tabela: {str(e)}")
        
    # Processando entradas de texto
    else:
        if tabela_atividade  and tabela_risco:  # sempre envia as duas tabelas, mesmo que uma esteja vazia
            try:
                df_atv = pd.DataFrame(json.loads(tabela_atividade))
                df_atv.reset_index(drop=True,inplace=True)  # Resetar index, ponteiro
                df_riscos = pd.DataFrame(json.loads(tabela_risco))
                df_riscos.reset_index(drop=True,inplace=True)

                # Alterando nomes do Dataframe
                df_atv.rename(columns={
                    'Tipo_distribuição': 'Tipo de Distribuicao', 'T_otimista': 'Tempo Otimista', 'T_provavel': 'Tempo Provavel', 'T_pessimista': 'Tempo Pessimista',
                    'T_min': 'Tempo Minimo', 'T_moda': 'Tempo Moda', 'T_max': 'Tempo Maximo', 'T_medio': 'Tempo Mais Provavel', 'Custo_fixo': 'Custo Fixo', 'Custo_un_t': 'Custo por Unidade de Tempo'
                    }, inplace=True)
                df_riscos.rename(columns={
                    'Tipo_distribuição': 'Tipo de Distribuicao', 'Atividades_afetadas': 'Atividades Afetadas', 'Atraso_min': 'Atraso Minimo',
                    'Atraso_med': 'Atraso Medio', 'Atraso_max': 'Atraso Maximo', 'Custo_fixo_adicional': 'Custo Fixo Adicional'
                    }, inplace=True)

                # Removendo linhas ou conjuntos vazios
                df_atv = df_atv[~(df_atv.eq("").all(axis=1) | df_atv.isna().all(axis=1))]
                df_riscos = df_riscos[~(df_riscos.eq("").all(axis=1) | df_riscos.isna().all(axis=1))]

                atividades_dict, riscos_dict = parse_mc_csv(df_atv, df_riscos)

                # Coverter stirng em variáveis numéricas
                for atividade, valores in atividades_dict.items():
                    if 't_otimista' in valores:
                        if valores['t_otimista'] != None and valores['t_otimista'] != '':
                            valores['t_otimista'] = float(valores['t_otimista'])
                    if 't_provavel' in valores:
                        if valores['t_provavel'] != None and valores['t_provavel'] != '':
                            valores['t_provavel'] = float(valores['t_provavel'])
                    if 't_pessimista' in valores:
                        if valores['t_pessimista'] != None and valores['t_pessimista'] != '':
                            valores['t_pessimista'] = float(valores['t_pessimista'])
                    if 'custo' in valores:
                        if valores['custo'] != None and valores['custo'] != '':
                            valores['custo'] = int(valores['custo'])
                    if 'custo_fix' in valores:
                        if valores['custo_fix'] != None and valores['custo_fix'] != '':
                            valores['custo_fix'] = int(valores['custo_fix'])
                    if 'custo_un' in valores:
                        if valores['custo_un'] != None and valores['custo_un'] != '':
                            valores['custo_un'] = float(valores['custo_un'])
                    if 't_minimo' in valores:
                        if valores['t_minimo'] != None and valores['t_minimo'] != '':
                            valores['t_minimo'] = float(valores['t_minimo'])
                    if 't_moda' in valores:
                        if valores['t_moda'] != None and valores['t_moda'] != '':
                            valores['t_moda'] = float(valores['t_moda'])
                    if 't_maximo' in valores:
                        if valores['t_maximo'] != None and valores['t_maximo'] != '':
                            valores['t_maximo'] = float(valores['t_maximo'])
                    if 't_media' in valores:
                        if valores['t_media'] != None and valores['t_media'] != '':
                            valores['t_media'] = float(valores['t_media'])

                for risco, valores in riscos_dict.items():
                    if 'probabilidade' in valores:
                        if valores['probabilidade'] != None and valores['probabilidade'] != '':
                            valores['probabilidade'] = float(valores['probabilidade'])
                    if 'atraso_minimo' in valores:
                        if valores['atraso_minimo'] != None and valores['atraso_minimo'] != '':
                            valores['atraso_minimo'] = float(valores['atraso_minimo'])
                    if 'atraso_medio' in valores:
                        if valores['atraso_medio'] != None and valores['atraso_medio'] != '':
                            valores['atraso_medio'] = float(valores['atraso_medio'])
                    if 'atraso_maximo' in valores:
                        if valores['atraso_maximo'] != None and valores['atraso_maximo'] != '':
                            valores['atraso_maximo'] = float(valores['atraso_maximo'])
                    if 'custo_fix' in valores:
                        if valores['custo_fix'] != None and valores['custo_fix'] != '':
                            valores['custo_fix'] = float(valores['custo_fix'])
                    if 'custo' in valores:
                        if valores['custo'] != None and valores['custo'] != '':
                            valores['custo'] = int(valores['custo'])

            except pd.errors.EmptyDataError:
                raise HTTPException(status_code=400, detail="Tabela sem dados ou com dados faltantes")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar a tabela: {str(e)}")            
            
        else:
            if atividades:
                try:
                    atividades_dict = json.loads(atividades)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Erro ao decodificar atividades")
            
            if riscos:
                try:
                    riscos_dict = json.loads(riscos)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Erro ao decodificar riscos")

    # Remover resultados antigos
    for filename in os.listdir('./resultadosMontecarlo/'):
        file_path = os.path.join('./resultadosMontecarlo/', filename)
        if os.path.isfile(file_path) and filename != 'montecarlo.txt':
            os.remove(file_path)

    # Realizar a simulação de Monte Carlo
    resultados = simular_montecarlo(atividades_dict, riscos_dict, num_iteracoes)  # Passa o num_iteracoes para a função
    gerar_pdf(resultados, "./resultadosMontecarlo/relatorio.pdf")
    lista_imagens = resultados[:-1]  # Todas as imagens
    xls_path = resultados[-1]  # O caminho do arquivo Excel

    # Redirecionar para a página de resultados
    return RedirectResponse(url='/resultMontecarlo', status_code=303)

@app.get("/resultMontecarlo")
async def result_montecarlo(request: Request):
    # Coletar nomes das imagens geradas
    imagens = glob.glob("resultadosMontecarlo/*.png")

    # URL para o arquivo XLS
    xls_url = "/baixar-xls"

    return templates.TemplateResponse("resultMonteCarlo.html", {"request": request, "imagens": imagens, "xls_url": xls_url})

@app.get("/baixar-xls")
async def baixar_xls():
    file_path = "Modelo_Riscos.xlsx"
    return FileResponse(file_path, filename="Modelo_Riscos.xlsx")

@app.get("/listar-imagens")
async def listar_imagens():
    # Lista todas as imagens na pasta resultadosMontecarlo
    imagens = glob.glob("resultadosMontecarlo/*.png")  # Altere o padrão se necessário para outros tipos de imagem
    imagens = [os.path.basename(imagem) for imagem in imagens]
    return JSONResponse(content={"imagens": imagens})

def parse_mc_csv(df_atv, df_riscos):
    atividades = {}
    riscos = {}

    # Atividades
    for index, row in df_atv.iterrows():
        # Garante que 'Precedentes' seja tratado corretamente
        precedentes = row['Precedentes']
        if isinstance(precedentes, str):  # Verifica se 'Precedentes' é uma string
            # Usa strip() para remover espaços em branco ao redor dos precedentes
            precedentes_list = [p.strip() for p in precedentes.split(',')] if precedentes else []
        else:
            precedentes_list = []  # Caso contrário, define como lista vazia

        if row['ID'] == "fim":
            atividades[row['ID']] = {
                "precedentes": precedentes_list,
                "duracao": 0,
                "custo_un": row.get('Custo por Unidade de Tempo', 0),
                "custo_fix": row.get('Custo Fixo', 0),
                }
       
        else:

            if row['Tipo de Distribuicao'] == "beta_pert":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_medio": row.get('Tempo Mais Provavel', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "custo_fix": row.get('Custo Fixo', 0),
                    "custo_un": row.get('Custo por Unidade de Tempo', 0),
                    }

            elif row['Tipo de Distribuicao'] == "triangular":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_medio": row.get('Tempo Mais Provavel', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "custo_fix": row.get('Custo Fixo', 0),
                    "custo_un": row.get('Custo por Unidade de Tempo', 0),
                }

            elif row['Tipo de Distribuicao'] == "uniforme":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "custo_fix": row.get('Custo Fixo', 0),
                    "custo_un": row.get('Custo por Unidade de Tempo', 0),
                }

            elif row['Tipo de Distribuicao'] == "normal":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "media": row.get('Media', None),
                    "d_p": row.get('Desvio Padrao', 1),
                    "custo_fix": row.get('Custo Fixo', 0),
                    "custo_un": row.get('Custo por Unidade de Tempo', 0),
                }

            elif row['Tipo de Distribuicao'] == "bernoulli":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "prob_otimista": row.get('Probabilidade do Tempo Otimista', None),
                    "custo_fix": row.get('Custo Fixo', 0),
                    "custo_un": row.get('Custo por Unidade de Tempo', 0),
                }
            

    # Risco
    if not df_riscos.empty:  # riscos são inputs opcionais
        for index, row in df_riscos.iterrows():
            if row['Tipo de Distribuicao da Consequencia'] == "triangular":
                riscos[row['ID']] = {
                "probabilidade": row['Probabilidade do Risco Ocorrer'],
                "tipo_dist": row['Tipo de Distribuicao da Consequencia'],
                "tipo": row['Tipo de Risco'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_medio": row.get('Atraso Medio', None),
                "atraso_maximo": row.get('Atraso Maximo', None),
                "custo_fix": row.get('Custo Fixo Adicional', 0),
                "custo_var": row.get('Custo Variavel Adicional', 0),

            }

            elif row['Tipo de Distribuicao da Consequencia'] == "uniforme":
                riscos[row['ID']] = {
                "probabilidade": row['Probabilidade do Risco Ocorrer'],
                "tipo_dist": row['Tipo de Distribuicao da Consequencia'],
                "tipo": row['Tipo de Risco'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_maximo": row.get('Atraso Maximo', None),
                "custo_fix": row.get('Custo Fixo Adicional', 0),
                "custo_var": row.get('Custo Variavel Adicional', 0),

            }

            elif row['Tipo de Distribuicao da Consequencia'] == "bernoulli":
                riscos[row['ID']] = {
                "probabilidade": row['Probabilidade do Risco Ocorrer'],
                "tipo_dist": row['Tipo de Distribuicao da Consequencia'],
                "tipo": row['Tipo de Risco'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_maximo": row.get('Atraso Maximo', None),
                "prob_otimista": row.get('Probabilidade do Atraso Otimista', None),
                "custo_fix": row.get('Custo Fixo Adicional', 0),
                "custo_var": row.get('Custo Variavel Adicional', 0),

            }

    return atividades, riscos

@app.post("/analyzePERT")
async def analyzePERT(atividades: str = Form(None), tabela: str = Form(None), csv_file: UploadFile = File(None), xlsx_file: UploadFile = File(None)):
    atividades_dict = {}

    # Processando arquivos CSV
    if csv_file and csv_file.filename:
        content = await csv_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio")

        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            atividades_dict = parse_pert_csv(df)
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Arquivo CSV sem dados ou mal formatado")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o CSV: {str(e)}")

    # Processando arquivos XLSX
    elif xlsx_file and xlsx_file.filename:
        try:
            content = await xlsx_file.read()
            excel_file = io.BytesIO(content)
            excel_df = pd.read_excel(excel_file, engine='openpyxl') # converter em dataframe
            csv_buffer = io.StringIO()
            excel_df.to_csv(csv_buffer, index=False)  # converter para csv, evitando formatações ocultas
            csv_buffer.seek(0)
            df = pd.read_csv(csv_buffer)

            if df.empty:
                raise HTTPException(status_code=400, detail="Arquivo XLSX vazio ou mal formatado")
            atividades_dict = parse_pert_csv(df)  
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar a tabela: {str(e)}")
        
    # Processando entradas de texto
    else:
        if tabela:
            try:
                df = pd.DataFrame(json.loads(tabela))

                df = df[~(df == '').all(axis=1)]  # Remover linhas vazias
                df['Precedentes'] = df['Precedentes'].replace('', np.nan)  # Trocar valores vaziios por NaN
                df['t_otimista'] = df['t_otimista'].replace('', np.nan)
                df['t_pessimista'] = df['t_pessimista'].replace('', np.nan)
                df['t_provavel'] = df['t_provavel'].replace('', np.nan)
                df['t_otimista'] = pd.to_numeric(df['t_otimista'], errors='coerce')  # Converter strings em valores numericos
                df['t_pessimista'] = pd.to_numeric(df['t_pessimista'], errors='coerce')  
                df['t_provavel'] = pd.to_numeric(df['t_provavel'], errors='coerce')

                df.reset_index(drop=True, inplace=True)  # Resetar index, ponteiro

                atividades_dict = parse_pert_csv(df)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Tabela sem dados ou com dados faltantes")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar tabela: {str(e)}")
        
        else:
            if atividades:
                try:
                    atividades_dict = json.loads(atividades)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Erro ao decodificar atividades")


    # Chama a função de cálculo PERT
    imagem = calcular_pert(atividades_dict)  # Imagem do gráfico PERT gerada pela função

    # Redirecionar para a página de resultados
    return RedirectResponse(url='/resultPERT', status_code=303)

@app.get("/resultPERT")
async def result_pert(request: Request):
    # Coleta a imagem gerada
    imagem_pert = "resultadosPert/atividades_pert.png"  # Caminho da imagem gerada

    return templates.TemplateResponse("resultPert.html", {"request": request, "imagem": imagem_pert})

# Função para parse de CSV
def parse_pert_csv(df):
    atividades = {}
    for index, row in df.iterrows():
        # Verifica se a atividade é 'fim'
        if row['Atividade'] == "fim":
            atividades[row['Atividade']] = {
                "precedentes": row['Precedentes'].split(',') if isinstance(row['Precedentes'], str) and row['Precedentes'] else [],
                "duracao": 0  # Define a duração como 0 para a atividade 'fim'
            }
        else:
            atividades[row['Atividade']] = {
                "precedentes": row['Precedentes'].split(',') if isinstance(row['Precedentes'], str) and row['Precedentes'] else [],
                "t_otimista": int(row['t_otimista']) if pd.notna(row['t_otimista']) else None,
                "t_provavel": int(row['t_provavel']) if pd.notna(row['t_provavel']) else None,
                "t_pessimista": int(row['t_pessimista']) if pd.notna(row['t_pessimista']) else None,
            }

    return atividades

@app.get("/download_png")
async def download_png():
    file_path = "resultadosPert/atividades_pert.png" 
    return FileResponse(file_path, filename="pert_image.png")

@app.get("/download_xls")
async def download_xls():
    # Substitua o caminho pelo caminho real do arquivo XLS gerado
    file_path = "caminho/para/o/seu/arquivo.xlsx"
    return FileResponse(file_path, filename="resultado_pert.xlsx")

@app.post("/calculo_tempo")
async def calculo_tempo(data: dict):
    # Lógica para processar os dados do formulário
    return {"message": "Cálculo realizado com sucesso!"}

@app.post("/gauss")
async def gauss(data: dict):
    # Lógica para processar o formulário
    return {"message": "Cálculo Gaussiano realizado com sucesso!"}

@app.post("/analyze")
async def analyzeCPM(atividades: str = Form(None), tabela: str = Form(None), csv_file: UploadFile = File(None), xlsx_file: UploadFile = File(None)):
    atividades_dict = {}

    # Processando arquivos CSV
    if csv_file and csv_file.filename:
        content = await csv_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio")

        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            atividades_dict = parse_cpm_csv(df)

        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Arquivo CSV sem dados ou mal formatado")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o CSV: {str(e)}")

    # Processando arquivos XLSX
    elif xlsx_file and xlsx_file.filename:
        try:
            content = await xlsx_file.read()
            excel_file = io.BytesIO(content)
            excel_df = pd.read_excel(excel_file, engine='openpyxl') # converter em dataframe
            csv_buffer = io.StringIO()
            excel_df.to_csv(csv_buffer, index=False)  # converter para csv, evitando formatações ocultas
            csv_buffer.seek(0)
            df = pd.read_csv(csv_buffer)

            if df.empty:
                raise HTTPException(status_code=400, detail="Arquivo XLSX vazio ou mal formatado")
            atividades_dict = parse_cpm_csv(df)  
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar a tabela: {str(e)}")
    
    # Processando entradas de texto
    else:
        if tabela:
            try:
                df = pd.DataFrame(json.loads(tabela))

                df = df[~(df == '').all(axis=1)]  # Remover linhas vazias
                df['Precedentes'] = df['Precedentes'].replace('', np.nan)  # Trocar valores vazios por NaN
                df['Duracao'] = pd.to_numeric(df['Duracao'], errors='coerce')  # Converter strings em números
        
                df.reset_index(drop=True, inplace=True)  # Resetar index, ponteiro

                atividades_dict = parse_cpm_csv(df)  

            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Tabela sem dados ou com dados faltantes")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar a tabela: {str(e)}")
            
        else:
            if atividades:
                try:
                    atividades_dict = json.loads(atividades)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Erro ao decodificar atividades")


    # Chama a função de cálculo CPM
    imagem = calcular_cpm(atividades_dict)

    # Redirecionar para a página de resultados
    return RedirectResponse(url='/result', status_code=303)

@app.post("/analyze")
async def analyze(atividades: str = Form(None), csv_file: UploadFile = File(None)):
    atividades_dict = {}

    # Processando arquivos CSV
    if csv_file and csv_file.filename:
        content = await csv_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio")

        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            atividades_dict = parse_cpm_csv(df)
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Arquivo CSV sem dados ou mal formatado")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o CSV: {str(e)}")

    # Processando entradas de texto
    else:
        if atividades:
            try:
                atividades_dict = json.loads(atividades)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Erro ao decodificar atividades")

    # Chama a função de cálculo CPM
    imagem = calcular_cpm(atividades_dict)
    return RedirectResponse(url='/result', status_code=303)

@app.get("/result")
async def result_cpm(request: Request):
    imagem_cpm = "resultadosCpm/atividades_cpm.png"
    return templates.TemplateResponse("result.html", {"request": request, "imagem": imagem_cpm})

# Função para parse de CSV
def parse_cpm_csv(df):
    atividades = {}
    for index, row in df.iterrows():
        atividades[row['Atividade']] = {
            "precedentes": row['Precedentes'].split(',') if isinstance(row['Precedentes'], str) and row['Precedentes'] else [],
            "duracao": int(row['Duracao']) if pd.notna(row['Duracao']) else None,
        }
    return atividades

@app.get("/download_png")
async def download_cpm_png():
    file_path = "resultadosCPM/atividades_cpm.png"
    return FileResponse(file_path, filename="cpm_image.png")

@app.get("/download_xls_cpm", name="download_xls_cpm")
async def download_xls_cpm():
    file_path = "caminho/para/o/seu/arquivo_cpm.xlsx" 
    return FileResponse(file_path, filename="resultado_cpm.xlsx")



