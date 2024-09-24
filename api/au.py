import csv

atividades_pert = {
    "A": {"precedentes": [], "t_otimista": 2, "t_pessimista": 8, "t_provavel": 5},
    "B": {"precedentes": ["A"], "t_otimista": 3, "t_pessimista": 10, "t_provavel": 6},
    "C": {"precedentes": ["A"], "t_otimista": 1, "t_pessimista": 4, "t_provavel": 5},
    "D": {"precedentes": ["B"], "t_otimista": 4, "t_pessimista": 6, "t_provavel": 8},
    "E": {"precedentes": ["B"], "t_otimista": 8, "t_pessimista": 12, "t_provavel": 10},
    "F": {"precedentes": ["C"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
    "G": {"precedentes": ["D", "E"], "t_otimista": 7, "t_pessimista": 11, "t_provavel": 8},
    "H": {"precedentes": ["F"], "t_otimista": 3, "t_pessimista": 6, "t_provavel": 5},
    "fim": {"precedentes": ["G", "H"], "duracao": 0}  # Duração definida aqui
}

# Abrindo o arquivo CSV para escrita
with open('atividades_pert.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Escrevendo o cabeçalho
    writer.writerow(['Atividade', 'Precedentes', 't_otimista', 't_pessimista', 't_provavel'])
    
    # Iterando sobre o dicionário e escrevendo os dados no CSV
    for atividade, info in atividades_pert.items():
        precedentes = ','.join(info['precedentes']) if info['precedentes'] else ''
        t_otimista = info.get('t_otimista', '')
        t_pessimista = info.get('t_pessimista', '')
        t_provavel = info.get('t_provavel', '')

        # Não incluímos 'duracao' para atividades que não têm
        writer.writerow([atividade, precedentes, t_otimista, t_pessimista, t_provavel])

print("CSV gerado com sucesso!")
