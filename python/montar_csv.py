import csv

# Definir as atividades PERT
atividades_pert = {
    "1": {"precedentes": [], "tipo": "beta_pert", "t_otimista": 2, "t_provavel": 5, "t_pessimista": 8, "custo": 0, "descricao": "descricao da atividade"},
    "2": {"precedentes": ["1"], "tipo": "triangular", "t_minimo": 3, "t_moda": 6, "t_maximo": 10, "custo": 0, "descricao": "descricao da atividade"},
    "3": {"precedentes": ["1"], "tipo": "uniforme", "t_minimo": 1, "t_maximo": 4, "custo": 0, "descricao": "descricao da atividade"},
    "4": {"precedentes": ["2"], "tipo": "normal", "t_otimista": 4, "t_media": 6, "t_pessimista": 8, "custo": 0, "descricao": "descricao da atividade"},
    "5": {"precedentes": ["2"], "tipo": "beta_pert", "t_otimista": 8, "t_provavel": 10, "t_pessimista": 12, "custo": 0, "descricao": "descricao da atividade"},
    "6": {"precedentes": ["3"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0, "descricao": "descricao da atividade"},
    "7": {"precedentes": ["4", "5"], "tipo": "beta_pert", "t_otimista": 7, "t_provavel": 8, "t_pessimista": 11, "custo": 0, "descricao": "descricao da atividade"},
    "8": {"precedentes": ["6"], "tipo": "beta_pert", "t_otimista": 3, "t_provavel": 5, "t_pessimista": 6, "custo": 0, "descricao": "descricao da atividade"},
    "fim": {"precedentes": ["7", "8"], "tipo": "beta_pert", "duracao": 0, "custo": 0, "descricao": "descricao da atividade"}
}

# Definir os riscos
riscos = {
    "A": {"probabilidade": 0.5, "tipo": "triangular", "atividades_afetadas": ["1"], "atraso_minimo": 3, "atraso_medio": 4, "atraso_maximo": 5},
    "B": {"probabilidade": 0.3, "tipo": "uniforme", "atividades_afetadas": ["2", "3"], "atraso_minimo": 3, "atraso_maximo": 5}
}

# Nome do arquivo CSV de saída
csv_file = "atividades_e_riscos.csv"

# Criar o arquivo CSV
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)

    # Escrever o cabeçalho
    writer.writerow(["Tipo", "ID", "Precedentes", "Tipo de Distribuicao", "Tempo Otimista", "Tempo Provavel", 
                     "Tempo Pessimista", "Tempo Minimo", "Tempo Moda", "Tempo Maximo", "Tempo Medio", "Custo", 
                     "Probabilidade", "Atividades Afetadas", "Atraso Minimo", "Atraso Medio", "Atraso Maximo", "Descricao"])

    # Escrever as atividades PERT no CSV
    for id_atividade, atividade in atividades_pert.items():
        writer.writerow([
            "Atividade", 
            id_atividade, 
            ', '.join(atividade["precedentes"]), 
            atividade["tipo"], 
            atividade.get("t_otimista", ""), 
            atividade.get("t_provavel", ""), 
            atividade.get("t_pessimista", ""), 
            atividade.get("t_minimo", ""), 
            atividade.get("t_moda", ""), 
            atividade.get("t_maximo", ""), 
            atividade.get("t_media", ""),  # Novo campo para incluir o tempo médio
            atividade["custo"], 
            "", "", "", "", "", 
            atividade["descricao"]
        ])

    # Escrever os riscos no CSV
    for id_risco, risco in riscos.items():
        writer.writerow([
            "Risco", 
            id_risco, 
            "", 
            risco["tipo"], 
            "", "", "", 
            risco.get("atraso_minimo", ""), 
            "", 
            risco.get("atraso_maximo", ""), 
            "",  # Tempo médio não aplicável para riscos
            "",  # Custo não aplicável para riscos
            risco["probabilidade"], 
            ', '.join(risco["atividades_afetadas"]), 
            risco.get("atraso_minimo", ""), 
            risco.get("atraso_medio", ""), 
            risco.get("atraso_maximo", ""), 
            ""
        ])

print(f"CSV '{csv_file}' criado com sucesso!")
