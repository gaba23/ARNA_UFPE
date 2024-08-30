from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
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
import shutil

templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

generated_images = []
generated_planilha = ""

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
    # Lógica para deslogar o usuário
    return RedirectResponse(url="/", status_code=303)

@app.post("/analyzeMonteCarlo")
async def analyzeMonteCarlo(request: Request, atividades: str = Form(None), riscos: str = Form(None), 
                            csv_file: UploadFile = File(None), json_file: UploadFile = File(None)):
    atividades_dict = {}
    riscos_dict = {}
    
    # Processamento de arquivos CSV
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
    
    # Processamento de arquivos JSON
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

    # Processamento de entradas de texto
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

    # Simulação de Monte Carlo
    imagens, planilha_path = simular_montecarlo(atividades_dict, riscos_dict)
    
    # Mover arquivos para a pasta static
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    for imagem in imagens:
        shutil.move(imagem, os.path.join(static_dir, os.path.basename(imagem)))

    shutil.move(planilha_path, os.path.join(static_dir, os.path.basename(planilha_path)))

    # Armazena os caminhos para o retorno
    global generated_images, generated_planilha
    generated_images = [os.path.basename(imagem) for imagem in imagens]
    generated_planilha = os.path.basename(planilha_path)

    # Redirecionar para a página de resultados
    return RedirectResponse(url='/resultMonteCarlo', status_code=303)

# Função para parse de CSV
def parse_csv(df):
    atividades = {}
    riscos = {}
    # Exemplo básico de como mapear CSV para dicionários
    # Aqui você ajusta para o formato do CSV real
    for index, row in df.iterrows():
        atividades[row['atividade']] = {
            "precedentes": row['precedentes'].split(',') if row['precedentes'] else [],
            "tipo": row['tipo'],
            "t_otimista": row.get('t_otimista', None),
            "t_provavel": row.get('t_provavel', None),
            "t_pessimista": row.get('t_pessimista', None),
            "custo": row.get('custo', 0)
        }
        # Para os riscos, assumindo que eles estão em colunas diferentes
        if 'riscos' in row and pd.notna(row['riscos']):
            riscos[row['atividade']] = {
                "probabilidade": row['probabilidade'],
                "tipo": row['tipo_risco'],
                "atividades_afetadas": row['atividades_afetadas'].split(','),
                "atraso_minimo": row['atraso_minimo'],
                "atraso_medio": row.get('atraso_medio', None),
                "atraso_maximo": row['atraso_maximo']
            }
    return atividades, riscos

# Função para parse de texto para atividades
def parse_text_atividades(text):
    atividades = {}
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            parts = line.split(':')
            atividade = parts[0].strip()
            detalhes = eval(parts[1].strip())  # Supondo que os detalhes venham como dict-like
            atividades[atividade] = detalhes
    return atividades

# Função para parse de texto para riscos
def parse_text_riscos(text):
    riscos = {}
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            parts = line.split(':')
            risco = parts[0].strip()
            detalhes = eval(parts[1].strip())  # Supondo que os detalhes venham como dict-like
            riscos[risco] = detalhes
    return riscos

@app.get("/resultMontecarlo")
async def result_montecarlo(request: Request):
    # Coletar nomes dos arquivos de imagens geradas
    imagem_diagrama = ["diagrama_atividades.png"]
    imagens_atividades = [img.split("/")[-1] for img in glob.glob("static/distribuicao_atividade_*.png")]
    imagens_caminhos = [img.split("/")[-1] for img in glob.glob("static/distribuicao_caminho_*.png")]
    imagem_projeto = ["distribuicao_duracao_projeto.png"]
    imagem_gantt = ["grafico_gantt.png"]
    imagem_tornado = ["grafico_tornado.png"]
    
    imagens = imagem_diagrama + imagens_atividades + imagens_caminhos + imagem_projeto + imagem_gantt + imagem_tornado

    # URL para o arquivo XLS
    xls_url = "/baixar-xls"

    return templates.TemplateResponse("resultMontecarlo.html", {"request": request, "imagens": imagens, "xls_url": xls_url})


@app.get("/baixar-xls")
async def baixar_xls():
    file_path = "static/Modelo_Riscos.xlsx"
    return FileResponse(file_path, filename="Modelo_Riscos.xlsx")

@app.get("/download_image/{imagem}")
async def download_image(imagem: str):
    file_path = f"static/{imagem}"
    return FileResponse(file_path, filename=imagem)

@app.get("/baixar-xls")
async def download_xls(request: Request):
    xls_path = "static/Modelo_Riscos.xlsx"
    return FileResponse(xls_path, filename="Modelo_Riscos.xlsx")

