from typing import Dict
from networkx import Graph

from src.Algorithms.AStar import AStar
from src.Algorithms.BFS import BFS
from src.Algorithms.Biderectional import Biderectional
from src.Algorithms.DFS import DFS
from src.Algorithms.IDS import IDS
from src.Domain.Delivery import Delivery
from src.Domain.Node import Node
from src.Domain.Search import Search, Algorithm


def get_algorithm(algorithm_enum: Algorithm) -> type(Search):  # converte um enum para a classe de busca a ser utilizada
    if algorithm_enum == Algorithm.AStar:
        return type(AStar)
    if algorithm_enum == Algorithm.BFS:
        return type(BFS)
    if algorithm_enum == Algorithm.Biderectional:
        return type(Biderectional)
    if algorithm_enum == Algorithm.IDS:
        return type(IDS)
    if algorithm_enum == Algorithm.DFS:
        return type(DFS)


class GraphHelper:  # classe para agrupar metodos de extensao do grafo
    def __init__(self, graph: Graph):
        self.graph: Graph = graph

    def get_nodes_data(self) -> Dict[str, list[Node]]:  # retorna os dados do grafo em um dicionario para ser transformado em json pela api
        return {f'{node.x},{node.y}': [adj.serialize() for adj in self.graph.adj[node]] for node in self.graph.nodes}

    def get_path(self, algorithm: type(Search), x: int, y: int) -> [Node]:  # retorna o caminho correto a partir dos dados enviados pela request do front end
        delivery_shelf = next(node for node in self.graph.nodes if node.x == x and node.y == y)
        return Delivery(delivery_shelf, algorithm).get_delivery_path()