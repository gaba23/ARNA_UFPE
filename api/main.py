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
import os
from pert import calcular_pert
import networkx as nx

templates = Jinja2Templates(directory="templates")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/resultadosMontecarlo", StaticFiles(directory="resultadosMontecarlo"), name="resultadosMontecarlo")

app.mount("/resultadosPert", StaticFiles(directory="resultadosPert"), name="resultadosPert")

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
    return templates.TemplateResponse("homePert.html", {"request": request})

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
async def analyzeMonteCarlo(request: Request, atividades: str = Form(None), riscos: str = Form(None), 
                            csv_file: UploadFile = File(None), json_file: UploadFile = File(None),
                            num_interacoes: int = Form(...)):  # Adicione o novo parâmetro aqui
    atividades_dict = {}
    riscos_dict = {}
    
    # Processando arquivos CSV
    if csv_file and csv_file.filename:
        content = await csv_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio")
        
        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            atividades_dict, riscos_dict = parse_csv(df)
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Arquivo CSV sem dados ou mal formatado")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao processar o CSV: {str(e)}")
    
    # Processando arquivos JSON
    elif json_file and json_file.filename:
        content = await json_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo JSON vazio")
        
        try:
            data = json.loads(content.decode('utf-8'))
            atividades_dict = data.get('atividades', {})
            riscos_dict = data.get('riscos', {})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Erro ao decodificar arquivo JSON")

    # Processando entradas de texto
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

    # Realizar a simulação de Monte Carlo
    resultados = simular_montecarlo(atividades_dict, riscos_dict, num_interacoes)  # Passa o num_interacoes para a função
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

    return templates.TemplateResponse("resultMontecarlo.html", {"request": request, "imagens": imagens, "xls_url": xls_url})

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

# Função para parse de CSV
def parse_csv(df):
    atividades = {}
    riscos = {}
    for index, row in df.iterrows():
        # Verifica se é uma atividade
        if row['Tipo'] == "Atividade":
            # Garante que 'Precedentes' seja tratado corretamente
            precedentes = row['Precedentes']
            if isinstance(precedentes, str):  # Verifica se 'Precedentes' é uma string
                # Usa strip() para remover espaços em branco ao redor dos precedentes
                precedentes_list = [p.strip() for p in precedentes.split(',')] if precedentes else []
            else:
                precedentes_list = []  # Caso contrário, define como lista vazia

            atividades[row['ID']] = {
                "precedentes": precedentes_list,
                "tipo": row['Tipo de Distribuicao'],
                "t_otimista": row.get('Tempo Otimista', None),
                "t_provavel": row.get('Tempo Provavel', None),
                "t_pessimista": row.get('Tempo Pessimista', None),
                "t_minimo": row.get('Tempo Minimo', None),
                "t_moda": row.get('Tempo Moda', None),
                "t_maximo": row.get('Tempo Maximo', None),
                "t_media": row.get('Tempo Medio', None),
                "custo": row.get('Custo', 0),
                "descricao": row.get('Descricao', "")
            }
        
        # Verifica se é um risco
        elif row['Tipo'] == "Risco":
            riscos[row['ID']] = {
                "probabilidade": row['Probabilidade'],
                "tipo": row['Tipo de Distribuicao'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_medio": row.get('Atraso Medio', None),
                "atraso_maximo": row.get('Atraso Maximo', None)
            }
    print(atividades)
    return atividades, riscos

def parse_csv(df):
    atividades = {}
    riscos = {}
    for index, row in df.iterrows():
        # Verifica se é uma atividade
        if row['Tipo'] == "Atividade":
            # Garante que 'Precedentes' seja tratado corretamente
            precedentes = row['Precedentes']
            if isinstance(precedentes, str):  # Verifica se 'Precedentes' é uma string
                # Usa strip() para remover espaços em branco ao redor dos precedentes
                precedentes_list = [p.strip() for p in precedentes.split(',')] if precedentes else []
            else:
                precedentes_list = []  # Caso contrário, define como lista vazia

            if row['Tipo de Distribuicao'] == "beta_pert":
                if row['ID'] == "fim":
                    atividades[row['ID']] = {
                        "precedentes": precedentes_list,
                        "tipo": row['Tipo de Distribuicao'],
                        "duracao": 0,
                        "custo": row.get('Custo', 0),
                        "descricao": row.get('Descricao', "")
                        }
                else:
                    atividades[row['ID']] = {
                        "precedentes": precedentes_list,
                        "tipo": row['Tipo de Distribuicao'],
                        "t_otimista": row.get('Tempo Otimista', None),
                        "t_provavel": row.get('Tempo Provavel', None),
                        "t_pessimista": row.get('Tempo Pessimista', None),
                        "custo": row.get('Custo', 0),
                        "descricao": row.get('Descricao', "")
                        }

            elif row['Tipo de Distribuicao'] == "triangular":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_moda": row.get('Tempo Moda', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "custo": row.get('Custo', 0),
                    "descricao": row.get('Descricao', "")
                }

            elif row['Tipo de Distribuicao'] == "uniforme":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_minimo": row.get('Tempo Minimo', None),
                    "t_maximo": row.get('Tempo Maximo', None),
                    "custo": row.get('Custo', 0),
                    "descricao": row.get('Descricao', "")
                }

            elif row['Tipo de Distribuicao'] == "normal":
                atividades[row['ID']] = {
                    "precedentes": precedentes_list,
                    "tipo": row['Tipo de Distribuicao'],
                    "t_otimista": row.get('Tempo Otimista', None),
                    "t_pessimista": row.get('Tempo Pessimista', None),
                    "t_media": row.get('Tempo Medio', None),
                    "custo": row.get('Custo', 0),
                    "descricao": row.get('Descricao', "")
                }
        
        # Verifica se é um risco
        elif row['Tipo'] == "Risco":
            if row['Tipo de Distribuicao'] == "triangular":
                riscos[row['ID']] = {
                "probabilidade": row['Probabilidade'],
                "tipo": row['Tipo de Distribuicao'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_medio": row.get('Atraso Medio', None),
                "atraso_maximo": row.get('Atraso Maximo', None)
            }

            elif row['Tipo de Distribuicao'] == "uniforme":
                riscos[row['ID']] = {
                "probabilidade": row['Probabilidade'],
                "tipo": row['Tipo de Distribuicao'],
                "atividades_afetadas": [a.strip() for a in row['Atividades Afetadas'].split(',')] if isinstance(row['Atividades Afetadas'], str) else [],
                "atraso_minimo": row.get('Atraso Minimo', None),
                "atraso_maximo": row.get('Atraso Maximo', None)
            }
    # print(atividades)
    return atividades, riscos

@app.post("/analyzePERT")
async def analyzePERT(atividades: str = Form(None), csv_file: UploadFile = File(None), json_file: UploadFile = File(None)):
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

    # Processando arquivos JSON
    elif json_file and json_file.filename:
        content = await json_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo JSON vazio")

        try:
            atividades_dict = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Erro ao decodificar arquivo JSON")

    # Processando entradas de texto
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
        atividades[row['atividade']] = {
            "precedentes": row['precedentes'].split(',') if row['precedentes'] else [],
            "t_otimista": row.get('t_otimista', None),
            "t_provavel": row.get('t_provavel', None),
            "t_pessimista": row.get('t_pessimista', None),
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

