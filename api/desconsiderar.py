from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
#from montecarlo import simular_montecarlo
import json
import csv
import io
import pandas as pd

templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.post("/analyze")
async def analyze(
    request: Request,
    atividades: str = Form(...),
    riscos: str = Form(...),
    csv_file: UploadFile = File(None),
    json_file: UploadFile = File(None)
):
    atividades_texto = atividades.strip()
    riscos_texto = riscos.strip()

    atividades_variavel = None
    riscos_variavel = None

    try:
        # Verificar se um arquivo CSV foi enviado
        if csv_file:
            csv_content = await csv_file.read()
            csv_data = csv.reader(io.StringIO(csv_content.decode('utf-8')))
            # Processar o CSV e extrair atividades e riscos
            atividades_variavel, riscos_variavel = process_csv(csv_data)
        
        # Verificar se um arquivo JSON foi enviado
        elif json_file:
            json_content = await json_file.read()
            json_data = json.loads(json_content.decode('utf-8'))
            # Processar o JSON e extrair atividades e riscos
            atividades_variavel, riscos_variavel = process_json(json_data)

        # Se nenhum arquivo foi enviado, usar os dados de texto
        else:
            atividades_variavel = atividades_texto
            riscos_variavel = riscos_texto
        
        # Aqui você pode chamar a função de simulação Monte Carlo
        #resultado = simular_montecarlo(atividades_variavel, riscos_variavel)
        
        # Retornar o resultado ou redirecionar para uma página de resultados
        return templates.TemplateResponse("result.html", {"request": request, "resultado": "resultado"})

    except Exception as e:
        return templates.TemplateResponse("monteCarlo.html", {"request": request, "erro": str(e)})

def process_csv(csv_data):
    atividades = []
    riscos = []
    for row in csv_data:
        # Processar cada linha de acordo com a estrutura do seu CSV
        atividades.append(row[0])  # Exemplo, ajuste conforme necessário
        riscos.append(row[1])      # Exemplo, ajuste conforme necessário
    return atividades, riscos

def process_json(json_data):
    atividades = []
    riscos = []
    # Processar dados JSON conforme a estrutura esperada
    for item in json_data:
        atividades.append(item['atividade'])  # Exemplo, ajuste conforme necessário
        riscos.append(item['risco'])          # Exemplo, ajuste conforme necessário
    return atividades, riscos

@app.post("/monteCarlo")
async def montecarlo_calculo(
    request: Request,
    inputType: str = Form(...),
    inputData: str = Form(...),
    fileUpload: UploadFile = File(None)
):
    dados_processados = None

    if fileUpload:
        # Processar o arquivo enviado
        if fileUpload.filename.endswith(".json"):
            content = await fileUpload.read()
            dados_processados = json.loads(content)
        elif fileUpload.filename.endswith(".csv"):
            content = await fileUpload.read()
            content_str = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(content_str))
            dados_processados = [row for row in reader]
        else:
            return templates.TemplateResponse("monteCarlo.html", {"request": request, "resultado": {"erro": "Formato de arquivo não suportado"}})
    else:
        # Processar os dados fornecidos diretamente no formulário
        if inputType == "json":
            dados_processados = json.loads(inputData)
        elif inputType == "csv":
            reader = csv.DictReader(io.StringIO(inputData))
            dados_processados = [row for row in reader]
        elif inputType == "text":
            # Suponha que os dados textuais sejam enviados em um formato separado por linhas ou similar
            dados_processados = {"texto": inputData}
        else:
            return templates.TemplateResponse("monteCarlo.html", {"request": request, "resultado": {"erro": "Tipo de entrada não suportado"}})
    
    # Chamar a função de cálculo
    resultado = simular_montecarlo(dados_processados)
    
    # Retornar o resultado para o template
    return templates.TemplateResponse("monteCarlo.html", {"request": request, "resultado": resultado})
