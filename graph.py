from Map import Map
from zone import ZoneType


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
        self.used: int = 0

    def is_free(self) -> bool:
        """Checks whether it can accept one or more drones this turn."""
        return self.used < self.capacity

    def reset(self) -> None:
        """Resets the usage counter."""
        self.used = 0


class Node:
    """Represents a node in the graph, corresponding to a zone in the map.

    Attributes:
        name (str): The name of the node, corresponding to the zone name.
        edges (list[Edge]): A list of outgoing edges from this node.
    """
    def __init__(self, name: str, max_drones: int) -> None:
        """Initializes a Node instance.

        Args:
            name (str): The name of the node, corresponding to the zone name.
        """
        self.name: str = name
        self.max_drones: int = max_drones
        self.edges: list[Edge] = []
        self.drones_count: int = 0
        self.leaving: int = 0
        self.arriving: int = 0

    def free_capacity(self) -> int:
        """Remaining capacity after commiting a turn.

        Returns:
            Number of free slots for incomming drones.
        """
        net = self.drones_count - self.leaving
        return self.max_drones - net - self.arriving

    def get_edge(self, dst: str) -> Edge | None:
        """Get the outgoing edge to dst.

        Args:
            dst: The destination node's name.

        Returns:
            The edge if found or None if not.
        """
        return next((e for e in self.edges if e.to == dst), None)

    def reset(self) -> None:
        """Resets the per-turn flow counters."""
        self.leaving = 0
        self.arriving = 0

    def commit_turn(self) -> None:
        """Apply this turn's flow to the drone count."""
        self.drones_count += self.arriving - self.leaving


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
            self.nodes[name] = Node(name, self.map.zones[name].max_drones)

        self.nodes[self.map.start_zone].drones_count = self.map.nb_drones
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

    def reset(self) -> None:
        """Reset all counters per node and edge"""
        for node in self.nodes.values():
            node.reset()
            for edge in node.edges:
                edge.reset()

    def commit_turn(self) -> None:
        """Commit this turn's flow to all node's drone counts."""
        for node in self.nodes.values():
            node.commit_turn()

    def format_capacities(self) -> str:
        """Formats node and edge capacities for a turn.

        Returns:
            Multi-line string with one line per zone and one line per active
            edge.
        """
        lines: list[str] = []

        for name, node in self.nodes.items():
            lines.append(f"\t{name}: {node.drones_count}/{node.max_drones}")

        for node in self.nodes.values():
            for edge in node.edges:
                if edge.used > 0:
                    lines.append(
                        f"\t{node.name}-{edge.to}: {edge.used}/{edge.capacity}"
                        )
        return "\n".join(lines)
