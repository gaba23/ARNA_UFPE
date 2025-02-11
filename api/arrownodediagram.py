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
        self.event_mapping = {}  # Mapeia atividades (IDs) aos nós

    def generate_graph(self, last_activity):
        graph = Digraph()
        graph.attr(rankdir='LR')  # , splines='false')

        # Nós (Eventos)
        start_event_counter = 1
        end_event_counter = 1
        for dep in self.activity_dependencies:
            activity = dep.activity

            # Nós de entrada
            if dep.predecessors: # se houverem predecessores
                first_pred = dep.predecessors[0]  
                if first_pred in self.event_mapping:  # se o primeiro predecessor já foi mapeado
                    predecessor_end_event = self.event_mapping[first_pred][1]
                    start_event = f"{predecessor_end_event}"  # evento final do primeiro predecessor é o evento inicial da atividade
                else:  # primeiro evento não mapeado
                    start_event = f"E{start_event_counter}"
                    start_event_counter += 1
            else:  # primeiro nó
                start_event = f"E{start_event_counter}"
                start_event_counter += 1

            # Nós de saída
            end_event = f"E{end_event_counter + 1}"
            self.event_mapping[activity.id] = (start_event, end_event)
            end_event_counter += 1

            graph.node(start_event, shape="circle", label=start_event)
            graph.node(end_event, shape="circle", label=end_event)

            # Setas (Atividades)
            if activity.id == last_activity:
                edge_label = 'end'
            else:
                edge_label = f"{activity.id}"
            edge_color = "red" if activity.id in self.critical_activities else "black"  # caminho crítico em vermelho
            graph.edge(start_event, end_event, label=edge_label, color=edge_color)
        #  print(self.event_mapping)

        # Representação de dependências
        for dep in self.activity_dependencies:
            activity = dep.activity
            start_event, end_event = self.event_mapping[activity.id]
            for pred_id in dep.predecessors:
                pred_end_event = self.event_mapping[pred_id][1]
                if pred_end_event != start_event:  # impede a autoreferência das setas
                    graph.edge(pred_end_event, start_event, style="dotted")

        return graph

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

    # def read(self):
    #     activities = []
    #     critical_activities = set()

    #     with open(self.filepath, newline='') as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             activity_id = int(row['ActivityId'])
    #             duration = int(row['ActivityDuration']) if row['ActivityDuration'] else None
    #             predecessors = list(map(int, row['Predecessors'].split())) if row['Predecessors'] else []
    #             is_critical = row['Crucial'].strip().lower() == 'y'

    #             activity = Activity(activity_id, duration)
    #             activities.append(ActivityDependency(activity, predecessors))

    #             if is_critical:
    #                 critical_activities.add(activity_id)
    #     return activities, critical_activities

    def read(self):
        activities = []
        critical_activities = set()

        with open(self.filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                activity_id = int(row['ActivityId'])
                # duration = int(row['ActivityDuration']) if row['ActivityDuration'] else None
                predecessors = list(map(int, row['Predecessors'].split())) if row['Predecessors'] else []
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
    graph = generator.generate_graph(len(activities))

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
