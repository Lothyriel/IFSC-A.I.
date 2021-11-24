import os
from typing import Tuple, Optional

from flask import Flask
from flask_cors import CORS
from flask_restful import Api, reqparse
from guppy import hpy

from src.Domain.Cell import Cell
from src.Domain.Exceptions import IDSMaxDepth
from src.Domain.Search import Algorithm
from src.Extensions.GraphHelper import GraphHelper, get_algorithm
from src.Extensions.GraphTransformer import GraphTransformer, get_matrix_data

app = Flask(__name__)
cors = CORS(app)


def init_parser():  # inicia o new_parser dos headers do POST
    new_parser = reqparse.RequestParser()
    new_parser.add_argument('shelf_x', type=int, required=True)
    new_parser.add_argument('shelf_y', type=int, required=True)
    new_parser.add_argument('search_algorithm', type=int, required=True)
    new_parser.add_argument('max_depth', type=int, required=False)
    new_parser.add_argument('algorithm_a', type=int, required=False)
    new_parser.add_argument('algorithm_b', type=int, required=False)
    return new_parser


def get_kwargs(args: dict) -> dict:
    aa: Optional[int] = args['algorithm_a']
    ab: Optional[int] = args['algorithm_b']

    max_depth: Optional[int] = args['max_depth']

    algorithm_a: Optional[Algorithm] = Algorithm(aa) if type(aa) == int else None
    algorithm_b: Optional[Algorithm] = Algorithm(ab) if type(ab) == int else None
    return {"algorithm_a": algorithm_a, "algorithm_b": algorithm_b, "max_depth": max_depth}


@app.route('/api', methods=['GET'])
def get() -> Tuple[dict, int]:  # endpoint GET da api, retorna os dados do grafo
    app.logger.info('Pegando dados do grafo')

    data = {"nodes": helper.serialize_graph(),
            "x_limit": helper.node_matrix.shape[0],
            "y_limit": helper.node_matrix.shape[1],
            "robots": [n.serialize() for n in graph.nodes if n.robot_number],
            "search_instructions": {
                "algorithm_enum_values": {e.value: e.name for e in Algorithm},
                "request_headers": {'shelf_x': 'int', 'shelf_y': 'int', 'search_algorithm': 'Enum'},
                'biderectional_headers': {'algorithm_a': 'Enum', 'algorithm_b': 'Enum'},
                'IDS_headers': {'max_depth': 'int'}
            }
            }
    app.logger.info(f'Retornando dados do grafo')
    return data, 200


@app.route('/api', methods=['POST'])
def post():  # retorna caminho das buscas conforme o header da request
    h = hpy()
    app.logger.info(f'Memória utilizada: {h.heap().size / 1000000} MB')
    args = parser.parse_args()

    x: int = args['shelf_x']
    y: int = args['shelf_y']
    algorithm: Algorithm = Algorithm(args['search_algorithm'])

    kwargs = get_kwargs(args)

    ok, message = ensure_valid_delivery(x, y, algorithm, kwargs)

    if not ok:
        return {"error_message": message}, 400

    delivery = helper.get_delivery(algorithm, x, y, kwargs)

    try:
        app.logger.info(f'Iniciando busca {algorithm.name} da prateleira x:{x}, y:{y}')
        delivery.get_path()
        app.logger.info(f'Memória utilizada: {h.heap().size/1000000} MB')
        app.logger.info(f'Busca Finalizada: {algorithm.name} | da prateleira x:{x}, y:{y}')
    except IDSMaxDepth:
        return {'failed': 'IDS couldnt find a path with this max depth value',
                              'max_depth': kwargs["max_depth"],
                              'robot': delivery.shelf.robot_number,
                              'shelf': delivery.shelf.serialize(),
                              'search_algorithm': algorithm.value
                              }, 206

    data = {'search_path': [node.serialize() for node in delivery.path],
            'robot': delivery.shelf.robot_number,
            'shelf': delivery.shelf.serialize(),
            'path_length': len(delivery.path),
            'search_algorithm': algorithm.value
            }

    return data, 200


def ensure_valid_delivery(x: int, y: int, algorithm: Algorithm, kwargs: dict) -> Tuple[bool, Optional[str]]:
    shelf = next(n for n in graph.nodes if n.x == x and n.y == y)
    if shelf.cell_type is not Cell.SHELF:
        return False, f"{x},{y} are not coordinates of a shelf"  # lança um bad request se as coordenadas enviadas não forem de uma prateleira
    if algorithm == Algorithm.IDS and not kwargs["max_depth"]:
        return False, "Cant do a IDS search without a max depth value"  # lança um bad request se for selecionado busca IDS sem o valor maximo de profundidade
    if algorithm == Algorithm.Biderectional:
        if kwargs["algorithm_a"] == Algorithm.Biderectional or kwargs["algorithm_b"] == Algorithm.Biderectional:
            return False, "Cant do a bidirectional search with biderectional search"  # lança um bad request se for selecionado busca bidirecional com busca bidirecional
        elif not (kwargs["algorithm_a"] and kwargs["algorithm_b"]):
            return False, "Cant do a bidirectional search without two algorithms"
        else:
            kwargs["algorithm_a"] = get_algorithm(kwargs["algorithm_a"])
            kwargs["algorithm_b"] = get_algorithm(kwargs["algorithm_b"])

    return True, None


if __name__ == '__main__':  # inicializando o grafo com uma matriz guardada no arquivo csv local
    port = int(os.environ.get("PORT", 5000))
    api = Api(app)
    parser = init_parser()

    node_matrix = get_matrix_data("armazem.csv")
    graph = GraphTransformer(node_matrix).create_graph()
    helper = GraphHelper(graph, node_matrix)

    app.run(host='0.0.0.0', port=port, debug=True)
