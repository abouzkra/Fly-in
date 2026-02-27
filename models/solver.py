from typing import List, Dict, Tuple
import heapq
from models import ZoneType


class Edge:
    def __init__(self, to: str, cost: float, capacity: int):
        self.to = to
        self.cost = cost
        self.capacity = capacity
        self.original_capacity = capacity

class Node:
    def __init__(self, name: str):
        self.name = name
        self.edges: List[Edge] = []


class InternalGraph:
    PRIORITY_BONUS = -0.01

    def __init__(self, map_):
        self.map = map_
        self.nodes: Dict[str, Node] = {}
        self._build_graph()

    def _build_graph(self):
        # Step 1: node splitting for capacity
        for zone in self.map.zones.values():
            if zone.zone_type == ZoneType.BLOCKED:
                continue

            in_node = f"{zone.name}_in"
            out_node = f"{zone.name}_out"
            self.add_node(in_node)
            self.add_node(out_node)

            cost = self._zone_cost(zone)
            self.add_edge(in_node, out_node, cost, zone.max_drones)

        # Step 2: connections
        for zone in self.map.zones.values():
            if zone.zone_type == ZoneType.BLOCKED:
                continue
            for neighbor in zone.neighbors:
                if self.map.zones[neighbor.name].zone_type == ZoneType.BLOCKED:
                    continue
                u = f"{zone.name}_out"
                v = f"{neighbor.name}_in"
                self.add_edge(u, v, 0, neighbor.link_capacity)

    def add_node(self, name: str):
        if name not in self.nodes:
            self.nodes[name] = Node(name)

    def add_edge(self, u: str, v: str, cost: float, capacity: int):
        self.nodes[u].edges.append(Edge(v, cost, capacity))

    def _zone_cost(self, zone):
        if zone.zone_type == ZoneType.RESTRICTED:
            return 2
        if zone.zone_type == ZoneType.PRIORITY:
            return 1 + self.PRIORITY_BONUS
        return 1


class SuurballeEngine:
    def __init__(self, graph: InternalGraph, start_zone: str, end_zone: str):
        self.graph = graph
        self.start = f"{start_zone}_out"
        self.end = f"{end_zone}_in"

    def find_all_disjoint_paths(self) -> List[List[str]]:
        paths = []
        while True:
            path = self._suurballe_once()
            if not path:
                break
            paths.append(self._strip_node_suffix(path))
        return paths

    def _suurballe_once(self) -> List[str] | None:
        dist, parent = self._dijkstra()
        if self.end not in parent:
            return None

        path = self._reconstruct_path(parent)
        self._consume_capacity(path)
        self._reverse_path_edges(path)
        return path

    def _dijkstra(self):
        dist = {node: float('inf') for node in self.graph.nodes}
        parent = {}
        dist[self.start] = 0
        heap = [(0, self.start)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue

            for edge in self.graph.nodes[u].edges:
                if edge.capacity <= 0:
                    continue
                v = edge.to
                new_dist = dist[u] + edge.cost
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    parent[v] = u
                    heapq.heappush(heap, (new_dist, v))
        return dist, parent

    def _reconstruct_path(self, parent: dict) -> List[str]:
        path = []
        node = self.end
        while node != self.start:
            path.append(node)
            node = parent[node]
        path.append(self.start)
        path.reverse()
        return path

    def _consume_capacity(self, path: List[str]):
        for u, v in zip(path, path[1:]):
            edge = next(e for e in self.graph.nodes[u].edges if e.to == v)
            edge.capacity -= 1

    def _reverse_path_edges(self, path: List[str]):
        for u, v in zip(path, path[1:]):
            edge = next(e for e in self.graph.nodes[u].edges if e.to == v)
            self.graph.nodes[u].edges.remove(edge)
            self.graph.add_edge(v, u, 0, 1)

    def _strip_node_suffix(self, path: List[str]) -> List[str]:
        stripped = []
        for n in path:
            if n.endswith("_in"):
                stripped.append(n[:-3])
            if n.endswith("_out"):
                stripped.append(n[:-4])
        final_path = []
        for z in stripped:
            if not final_path or z != final_path[-1]:
                final_path.append(z)
        return final_path


class PathDistributor:
    def __init__(self, paths: List[List[str]], nb_drones: int):
        self.paths = sorted(paths, key=len)
        self.nb_drones = nb_drones

    def assign(self) -> Dict[int, List[str]]:
        assignment = {}
        path_load = [0] * len(self.paths)

        for drone_id in range(1, self.nb_drones + 1):
            best_path = min(range(len(self.paths)), key=lambda i: len(self.paths[i]) + path_load[i])
            assignment[drone_id] = self.paths[best_path]
            path_load[best_path] += 1

        return assignment


class Drone:
    def __init__(self, id_: int, path: List[str]):
        self.id = id_
        self.path = path
        self.position = 0  # start at beginning

class TurnSimulator:
    def __init__(self, map_, drone_paths: dict[int, list[str]]):
        self.map = map_
        self.drones = [Drone(id_, path) for id_, path in drone_paths.items()]
        self.occupancy: dict[str, int] = {}  # track drones per zone

    def _all_finished(self) -> bool:
        return all(drone.position >= len(drone.path) - 1 for drone in self.drones)

    def _can_move(self, drone: Drone) -> bool:
        if drone.position >= len(drone.path) - 1:
            return False
        next_zone = drone.path[drone.position + 1]
        zone_capacity = self.map.zones[next_zone].max_drones
        return self.occupancy.get(next_zone, 0) < zone_capacity

    def run(self) -> list[list[tuple[int, str]]]:
        turns = []

        while not self._all_finished():
            turn_moves = []
            self.occupancy = {}

            for drone in self.drones:
                if self._can_move(drone):
                    drone.position += 1
                    zone = drone.path[drone.position]
                    turn_moves.append((drone.id, zone))
                    self.occupancy[zone] = self.occupancy.get(zone, 0) + 1

            if turn_moves:
                turns.append(turn_moves)

        return turns


class Solver:
    def __init__(self, map_):
        self.map = map_
        self.graph = InternalGraph(map_)
        self.paths: list[list[str]] = []
        self.drone_paths: dict[int, list[str]] = {}
        self.turns: list[list[tuple[int, str]]] = []

    def solve(self) -> list[list[tuple[int, str]]]:
        suurballe = SuurballeEngine(self.graph, self.map.start_zone, self.map.end_zone)
        self.paths = suurballe.find_all_disjoint_paths()
        print(self.paths)

        distributor = PathDistributor(self.paths, self.map.nb_drones)
        self.drone_paths = distributor.assign()

        simulator = TurnSimulator(self.map, self.drone_paths)
        self.turns = simulator.run()

        return self.turns
