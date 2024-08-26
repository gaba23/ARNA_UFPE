from fastapi import FastAPI
# pip install fastapi uvicorn
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

app = FastAPI()

# Definição das atividades
atividades_pert = {
    "A": {"precedentes": [], "tipo": "beta_pert", "t_otimista": 2, "t_provavel": 5, "t_pessimista": 8, "custo": 0},
    "B": {"precedentes": ["A"], "tipo": "triangular", "t_minimo": 3, "t_moda": 6, "t_maximo": 10, "custo": 0},
    "C": {"precedentes": ["A"], "tipo": "uniforme", "t_minimo": 1, "t_maximo": 4, "custo": 0},
    "D": {"precedentes": ["B"], "tipo": "normal", "t_otimista": 4, "t_media": 6, "t_pessimista": 8, "custo": 0},
    "E": {"precedentes": ["B"], "tipo": "beta_pert", "t_otimista": 8, "t_provavel": 10, "t_pessimista": 12, "custo": 0},
    "F": {"precedentes": ["C"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0},
    "G": {"precedentes": ["D", "E"], "tipo": "beta_pert", "t_otimista": 7, "t_provavel": 8, "t_pessimista": 11, "custo": 0},
    "H": {"precedentes": ["F"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0},
    "fim": {"precedentes": ["G", "H"], "tipo": "beta_pert", "duracao": 0, "custo": 0}
}

precedentes_atividades = {atividade: detalhes["precedentes"] for atividade, detalhes in atividades_pert.items()}

riscos = {
    "A": {"probabilidade": 0.5, "tipo": "triangular", "atividades_afetadas": ["A"], "atraso_minimo": 3, "atraso_medio": 4, "atraso_maximo": 5},
    "B": {"probabilidade": 0.3, "tipo": "uniforme", "atividades_afetadas": ["B", "C"], "atraso_minimo": 3, "atraso_maximo": 5}
}

riscos_ocorridos = {risco: [] for risco in riscos}
tempos_riscos = {risco: [] for risco in riscos}


# Adicionando um número ao nó e progredindo
mapa_atividades = {atividade: i + 2 for i, atividade in enumerate(atividades_pert.keys())}
mapa_atividades["inicio"] = 1

# Criação da lista que vai receber os dados no formato convertido
atividades_convertidas = []
