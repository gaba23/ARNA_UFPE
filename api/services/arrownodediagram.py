import csv
from collections import defaultdict
from graphviz import Digraph
import os

class EventNode:
    def __init__(self, event_id):
        self.id = event_id

class ActivityEdge:
    def __init__(self, activity_id, start_event, end_event):  #, duration=None):
        self.id = activity_id
        self.start_event = start_event
        self.end_event = end_event
        # self.duration = duration

class EventActivityGraphGenerator:
    def __init__(self, activity_dependencies, critical_activities):
        self.activity_dependencies = activity_dependencies
        self.critical_activities = critical_activities
        self.event_mapping = {}  # mapeia atividades (IDs) aos nós

    def reduction(self, graph):  # remove atividades extras geradas pelas dependências
        all_nodes = set()  # todos os nós
        used_nodes = set()  # nós com arestas conectadas
        for edge in graph.body:
            if '->' not in edge and '[' in edge:  # mapeia todos os nós
                node_name = edge.split()[0]
                all_nodes.add(node_name)
            
            if '->' in edge:  # identifica somente nós com aresta
                parts = edge.split('->')
                src = parts[0].strip()
                dst = parts[1].split()[0].strip()
                used_nodes.update([src, dst])

        unused_nodes = all_nodes - used_nodes  # nós sem arestas conectadas

        reduced_graph = graph
        for node in unused_nodes:
            reduced_graph.node(node, style="invisible")  # oculta nós flutuantes da representação

        return reduced_graph
    
    def generate_graph(self, last_activity):  # executor
        dict_duplicada, multiple_pred = self.map_graph(last_activity)
        return self.create_graph(dict_duplicada, multiple_pred, last_activity)

    def create_graph(self, dict_duplicada, multiple_pred, last_activity):  # cria grafo

        def value_in_dict(dict, target):  # retorna booleano para existência da atividade nos valores do dicionário  --> {'a': [1, 2]}
            return any(target in lista for lista in dict.values())
        
        # Cria Grafo
        graph = Digraph()
        graph.attr(rankdir='LR')

        # Nós (Eventos)
        start_event_counter, end_event_counter = 0, 0

        for dep in self.activity_dependencies:
            activity = dep.activity

            # Nós de entrada
            if dep.predecessors: # se houverem predecessores
                first_pred = dep.predecessors[0]  # predecessor primário
                if first_pred in self.event_mapping:  # se o primeiro predecessor já foi mapeado
                    predecessor_end_event = self.event_mapping[first_pred][1]
                    start_event = f"{predecessor_end_event}"  # evento final do primeiro predecessor é o evento inicial da atividade
        
                else:  # primeiro evento não mapeado
                    start_event = f"E{start_event_counter}"
                    start_event_counter += 1


            else:  # primeiro(s) nó(s)
                start_event = f"E0"
                start_event_counter += 1

            # Nós de saída
            end_event = f"E{end_event_counter + 1}"
            self.event_mapping[activity.id] = (start_event, end_event)
            end_event_counter += 1

            graph.node(start_event, shape="circle", label=start_event)
            if activity.id != last_activity:  # último nó (do evento de fim) é ignorado
                graph.node(end_event, shape="circle", label=end_event)

            # Setas (Atividades)
            if activity.id != last_activity:  # sem aresta pra atividade fim (dummy)
                edge_label = f"{activity.id}"
                edge_color = "red" if activity.id in self.critical_activities else "black"  # caminho crítico em vermelho

                if activity.id in multiple_pred:  
                    corrected_end_event = f'E{int(end_event[1:]) - 1}'

                    if value_in_dict(dict_duplicada, activity.id):  # atividade precisa de um dummy
                        dummy_event = f"E{end_event_counter}"  # redesigna end_event para tarefas que apontam para dummies
                        dummy_label = f"{end_event_counter}'"
                        graph.node(dummy_event, shape="circle", label=dummy_event)  # adiciona um nó intermediário

                        graph.edge(start_event, dummy_event, label=edge_label, color=edge_color)  # aresta da atividade secundária
                        graph.edge(dummy_event, corrected_end_event, label=dummy_label, style="dashed", arrowhead="normal")  # aresta dummy

                    else:  # atividade não precisa de um dummy
                        graph.edge(start_event, corrected_end_event, label=edge_label, color=edge_color)  

                else:
                    graph.edge(start_event, end_event, label=edge_label, color=edge_color)  # aresta regular

        return graph

    def map_graph(self, last_activity):  # mapeia elementos do grafo
        # Nós (Eventos)
        start_event_counter, end_event_counter, multiple_pred = 0, 0, []

        for dep in self.activity_dependencies:  # mapeia predecessores secundários (dependências)
            if len(dep.predecessors) > 1: 
                for p in dep.predecessors[1::]:
                    if p not in multiple_pred:
                        multiple_pred.append(p)

        node_map = {}  # mapeia atividades e nós ignorando o dummy

        for dep in self.activity_dependencies:
            activity = dep.activity

            # Nós de entrada
            if dep.predecessors: # se houverem predecessores
                first_pred = dep.predecessors[0]  # predecessor primário
                if first_pred in self.event_mapping:  # se o primeiro predecessor já foi mapeado
                    predecessor_end_event = self.event_mapping[first_pred][1]
                    start_event = f"{predecessor_end_event}"  # evento final do primeiro predecessor é o evento inicial da atividade
        
                else:  # primeiro evento não mapeado
                    start_event = f"E{start_event_counter}"
                    start_event_counter += 1

            else:  # primeiro(s) nó(s)
                start_event = f"E0"
                start_event_counter += 1

            # Nós de saída
            end_event = f"E{end_event_counter + 1}"
            self.event_mapping[activity.id] = (start_event, end_event)
            end_event_counter += 1

            # Setas (Atividades)
            if activity.id != last_activity:  # sem aresta pra atividade fim (dummy)
                if activity.id in multiple_pred:  # redesigna end_event para tarefas que apontam para dummies
                    corrected_end_event = f'E{int(end_event[1:]) - 1}'

                    node_map[activity.id] = [start_event, corrected_end_event]
                else:
                    node_map[activity.id] = [start_event, end_event]

        aresta_duplicada = defaultdict(list)

        for atv, no in node_map.items():
            aresta_duplicada[tuple(no)].append(atv)

        dict_duplicada = {valor: chave for valor, chave in aresta_duplicada.items() if len(chave) > 1}  # chave = aresta(nó inicial-final); valor = atividades com essa aresta

        return dict_duplicada, multiple_pred

class Activity:
    def __init__(self, activity_id):  # , duration=None):
        self.id = activity_id
        # self.duration = duration

class ActivityDependency:
    def __init__(self, activity, predecessors):
        self.activity = activity
        self.predecessors = predecessors

class ActivitiesReader:
    def __init__(self, filepath):
        self.filepath = filepath

    def read(self):
        activities = []
        critical_activities = set()

        with open(self.filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                activity_id = int(row['ActivityId'])
                # duration = int(row['ActivityDuration']) if row['ActivityDuration'] else None
                predecessors = list(map(int, row['Predecessors'].split())) if row['Predecessors'] else []
                predecessors.sort()  # ordena em ascendência para evitar identifcação incorreta de predecessores múltiplos primários e secundários
                is_critical = row['Crucial'].strip().lower() == 'y'

                activity = Activity(activity_id) #, duration)
                activities.append(ActivityDependency(activity, predecessors))

                if is_critical:
                    critical_activities.add(activity_id)
        return activities, critical_activities

class ArrowGraphWriter:
    def __init__(self, output_file):
        self.output_file = output_file

    def write(self, graph):
        graph.render(self.output_file, format='png', cleanup=True)

def create_arrow_diagram(input_file, output_file):
    # Ler
    reader = ActivitiesReader(input_file)
    activities, critical_activities = reader.read()

    # Gerar grafo
    generator = EventActivityGraphGenerator(activities, critical_activities)
    full_graph = generator.generate_graph(len(activities))

    graph = generator.reduction(full_graph)

    # Desenhar imagem 
    writer = ArrowGraphWriter(output_file)
    writer.write(graph)

# class CreateArrowDiagram:
#     def __init__(self, input_file, output_file):
#         self.input_file = input_file
#         self.output_file = output_file

#     def execute(self):
#         # Ler
#         reader = ActivitiesReader(self.input_file)
#         activities, critical_activities = reader.read()

#         # Gerar grafo
#         generator = EventActivityGraphGenerator(activities, critical_activities)
#         graph = generator.generate_graph()

#         # Desenhar imagem 
#         writer = ArrowGraphWriter(self.output_file)
#         writer.write(graph)

# if __name__ == "__main__":
#     input_file = "C:/Users/anama/OneDrive/Documents/Faculdade/Iniciação Científica/ARNA_UFPE/api/arrowdiagram/activities.csv"
#     output_file = "C:/Users/anama/OneDrive/Documents/Faculdade/Iniciação Científica/ARNA_UFPE/api/arrowdiagram/diagrama_na_seta"
#     diagram_creator = CreateArrowDiagram(input_file, output_file)
#     diagram_creator.execute()
