import abc
from enum import Enum
from typing import Dict, Tuple, Optional
from networkx import Graph

from src.Domain.Exceptions import EmptyBorder, AbstractSearch, DestinyFound
from src.Domain.Node import Node


class Search(metaclass=abc.ABCMeta):  # classe base para a implementacao das buscas
    def __init__(self, root: Node, destiny: list[Node], graph: Graph, kwargs: Optional[dict] = None):
        self.kwargs: dict = kwargs

        self.destiny: list[Node] = destiny
        self.root: Node = root
        self.graph: Graph = graph
        self.search_path: list[Node] = []
        self.border: list[Node] = [self.root]
        self.explored: Dict[Tuple[int, int]: Node] = {(self.root.x, self.root.y): self.root}
        self.current: Node = root

    def search(self) -> list[Node]:
        try:
            while True:
                self.do_one_step()
        except DestinyFound:
            return self.back_tracking()  # retorna o caminho final fazendo o backtracking

    def back_tracking(self) -> list[Node]:  # pega o ultimo nodo do caminho e percorre a lista do caminho de forma contrária atraves do nodo parente
        current = self.search_path[-1]      # até chegar no nodo inicial
        best_path = []

        while current:
            best_path.append(current)
            current = current.parent

        return best_path[::-1]

    def do_one_step(self) -> None:
        self.explore_current_node()
        self.explore_border()  # adiciona os nodos na fronteira do nodo escolhido para serem explorado

    def explore_current_node(self) -> None:
        if not self.border:
            raise EmptyBorder
        self.current = self.remove_choice()  # remove o proximo nodo da fronteira a ser percorrido com base no algoritmo escolhido
        self.explored[(self.current.x, self.current.y)] = self.current  # marcand o nodo escohido como explorado
        self.search_path.append(self.current)  # adicionando no caminho da busca
        if self.current in self.destiny:  # se for o destino
            raise DestinyFound  # lanca excessao de que o destino foi encontrado para ser tratada acima na stack
        self.explore_border()

    def explore_border(self) -> None:
        for adj in self.graph.adj[self.current]:
            if (adj.x, adj.y) not in self.explored and adj not in self.border:
                self.border.append(adj)
                adj.parent = self.current

    @abc.abstractmethod
    def remove_choice(self) -> Node:
        raise AbstractSearch("You need to inherit from this class and implement the search method")


class Algorithm(Enum):
    AStar = 0
    BFS = 1
    Biderectional = 2
    DFS = 3
    IDS = 4
