import matplotlib.pyplot as plt

# Dados do gráfico de Gantt
tasks = {
    'Tarefa 1': [0, 5],
    'Tarefa 2': [3, 7],
    'Tarefa 3': [5, 10],
    'Tarefa 4': [8, 12]
}

fig, ax = plt.subplots()

# Adicionar barras para cada tarefa
for i, (task, (start, end)) in enumerate(tasks.items()):
    ax.broken_barh([(start, end - start)], (i - 0.4, 0.8), facecolor='tab:blue')
    ax.text(start + (end - start) / 2, i, task, ha='center', va='center')

# Ajustar os limites do eixo y
ax.set_yticks(range(len(tasks)))
ax.set_yticklabels(tasks.keys())
ax.set_xlabel('Tempo')
ax.set_title('Gráfico de Gantt')

plt.show()