import webbrowser
import subprocess
import time
import os
import sys

def iniciar_fastapi():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Corrigir o path para o módulo FastAPI
    api_dir = os.path.join(dir_path, "api")  # Direciona para a pasta api
    sys.path.append(api_dir)  # Adiciona a pasta api ao sys.path

    main_module = "main:app"  # Módulo correto dentro da pasta `api`
    subprocess.Popen(["uvicorn", main_module, "--reload", "--app-dir", api_dir])  
    time.sleep(3)

def abrir_chrome():
    url = "http://127.0.0.1:8000"  # URL do seu FastAPI
    # Caminho do Chrome no sistema, você pode ajustar conforme o local de instalação
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
    webbrowser.get(chrome_path).open(url)

if __name__ == "__main__":
    # Mudar o diretório para a pasta onde está o FastAPI
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    iniciar_fastapi()  # Inicia o servidor FastAPI
    abrir_chrome()  # Abre o navegador Chrome na URL do FastAPI
