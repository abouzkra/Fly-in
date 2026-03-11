from ..parser.map import Map
from ..parser.zone import ZoneType


class Edge:
    """Represents a directed edge in the graph with a cost and capacity.

    Attributes:
        to (str): The name of the destination node.
        cost (float): The cost to traverse this edge.
        capacity (int): The maximum number of robots that can traverse this
            edge simultaneously.
        _original_capacity (int): The initial capacity of the edge, used for
            resetting after flow calculations.
    """
    def __init__(self, to: str, cost: float, capacity: int) -> None:
        """Initializes an Edge instance.

        Args:
            to (str): The name of the destination node.
            cost (float): The cost to traverse this edge.
            capacity (int): The maximum number of robots that can traverse this
                edge simultaneously.
        """
        self.to: str = to
        self.cost: float = cost
        self.capacity: int = capacity
        self._original_capacity: int = capacity


class Node:
    """Represents a node in the graph, corresponding to a zone in the map.

    Attributes:
        name (str): The name of the node, corresponding to the zone name.
        edges (list[Edge]): A list of outgoing edges from this node.
    """
    def __init__(self, name: str) -> None:
        """Initializes a Node instance.

        Args:
            name (str): The name of the node, corresponding to the zone name.
        """
        self.name: str = name
        self.edges: list[Edge] = []


MOVE_COST = {
    ZoneType.NORMAL: 1.0,
    ZoneType.RESTRICTED: 2.0,
    ZoneType.PRIORITY: 0.9,
    ZoneType.BLOCKED: float('inf'),
    }


class Graph:
    """Graph representation of the map, where nodes correspond to zones and
    edges represent possible movements between them.

    Attributes:
        map (Map): The original map object containing zone information.
        nodes (dict[str, Node]): A dictionary mapping zone names to their
            corresponding Node objects in the graph.
    """
    def __init__(self, parsed_map: Map) -> None:
        """Initializes a Graph instance from a parsed Map object.

        Args:
            parsed_map (Map): The parsed map object containing zone
                information.
        """
        self.map: Map = parsed_map
        self.nodes: dict[str, Node] = {}
        self._build()

    def _build(self) -> None:
        """Builds the graph from the map data, creating nodes and edges based
        on the zones and their neighbors."""
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
