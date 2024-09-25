import os
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading

# Função que executa o FastAPI usando uvicorn
def rodar_servidor():
    os.system("cd api && uvicorn main:app --reload")

# Função para abrir o navegador padrão
def abrir_navegador():
    webbrowser.open("http://127.0.0.1:8000")

# Função chamada quando o botão é clicado
def iniciar():
    # Cria uma thread para rodar o servidor em segundo plano
    threading.Thread(target=rodar_servidor).start()
    # Abre o navegador depois de iniciar o servidor
    abrir_navegador()

# Cria a janela principal do Tkinter
root = tk.Tk()
root.title("FastAPI Server")

# Adiciona um botão para iniciar o servidor
btn_iniciar = tk.Button(root, text="Iniciar Servidor", command=iniciar, width=25, height=2)
btn_iniciar.pack(pady=20)

# Executa a janela principal
root.mainloop()
