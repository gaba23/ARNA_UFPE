from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from main import simulacao_montecarlo
import json
import csv
import io

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
    resultado = simulacao_montecarlo(dados_processados)
    
    # Retornar o resultado para o template
    return templates.TemplateResponse("monteCarlo.html", {"request": request, "resultado": resultado})
