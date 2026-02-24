from models import Map, ZoneType


class Edge:
    def __init__(self, to: str, cost: float, capacity: int) -> None:
        self.to: str = to
        self.cost: float = cost
        self.capacity: int = capacity
        self._original_capacity: int = capacity


class Node:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.edges: list[Edge] = []


class Graph:
    def __init__(self, parsed_map: Map) -> None:
        self.map: Map = parsed_map
        self.nodes: dict[str, Node] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        for name, zone in self.map.zones.items():
            if zone.zone_type == ZoneType.BLOCKED:
                continue
            
            in_node = f"{name}_in"
            out_node = f"{name}_out"
            self._add_node(in_node)
            self._add_node(out_node)

            cost = 1.0
            if zone.zone_type == ZoneType.PRIORITY:
                cost -= 0.1
            elif zone.zone_type == ZoneType.RESTRICTED:
                cost = 2.0

            self._add_edge(in_node, out_node, cost, zone.max_drones)

        for name, zone in self.map.zones.items():
            if zone.zone_type == ZoneType.BLOCKED:
                continue

            for nb in zone.neighbors:
                if self.map.zones[nb.name].zone_type == ZoneType.BLOCKED:
                    continue

                u = f"{zone.name}_out"
                v = f"{nb.name}_in"
                self._add_edge(u, v, 0, nb.link_capacity)

    def _add_node(self, name: str) -> None:
        if not name in self.nodes:
            self.nodes[name] = Node(name)

    def _add_edge(self, u: str, v: str, cost: float, capacity: int) -> None:
        self.nodes[u].edges.append(Edge(v, cost, capacity))


class Solver:
    def __init__(self, parsed_map: Map) -> None:
        self.map: Map = parsed_map
        self.paths: list[list[str]] = []
        self.drone_assignments: dict[int, list[str]] = {}
        self.turns: list[list[tuple[int, str]]] = []
        
    def solve(self) -> None:
        pass
