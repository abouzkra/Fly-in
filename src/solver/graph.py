from ..parser.map import Map
from ..parser.zone import ZoneType


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


MOVE_COST = {
    ZoneType.NORMAL: 1.0,
    ZoneType.RESTRICTED: 2.0,
    ZoneType.PRIORITY: 0.9,
    ZoneType.BLOCKED: float('inf'),
    }


class Graph:
    def __init__(self, parsed_map: Map) -> None:
        self.map: Map = parsed_map
        self.nodes: dict[str, Node] = {}
        self._build()

    def _build(self) -> None:
        for name in self.map.zones:
            self.nodes[name] = Node(name)

        for zone in self.map.zones.values():
            for neigh in zone.neighbors:
                dest = self.map.zones[neigh.name]
                move_cost = MOVE_COST.get(dest.zone_type, float('inf'))
                self.nodes[zone.name].edges.append(
                    Edge(
                        neigh.name,
                        move_cost,
                        neigh.link_capacity
                        )
                    )
