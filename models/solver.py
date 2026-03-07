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

Path = list[str]
PathWithCost = tuple[Path, float]


class Solver:
    def __init__(self, parsed_map: Map) -> None:
        self.map: Map = parsed_map
        self.graph: Graph = Graph(parsed_map)
        self.paths: list[PathWithCost] = []
        self.drone_assignments: dict[int, Path] = {}
        self.turns: list[list[tuple[int, str]]] = []
        
    def solve(self) -> None:
        self._find_all_paths()
        self._assign_drones()
        self._schedule_drones()

    def _find_all_paths(self) -> None:
        start = self.map.start_zone
        end = self.map.end_zone

        if not start or not end:
            return

        res: list[PathWithCost] = []
        q: list[Path] = [[start]]
        visited: set[str] = {start}

        while q:
            curr_path = q.pop(0)
            curr_zone = curr_path[-1]

            if curr_zone == end:
                cost = self._path_cost(curr_path)
                if cost < float('inf'):
                    res.append((curr_path, cost))
                continue

            visited = visited.union(set(curr_path))
            node = self.graph.nodes.get(curr_zone)
            if not node:
                continue

            for edge in node.edges:
                neigh = edge.to

                if neigh in visited:
                    continue
                dest = self.map.zones.get(neigh)
                if not dest or dest.zone_type == ZoneType.BLOCKED:
                    continue
                q.append(curr_path + [neigh])

        self.paths = sorted(res, key=lambda p: p[1])

    def _path_cost(self, path: Path) -> float:
        cost = 0.
        cost += len(path)

        for zone_name in path:
            if self.map.zones[zone_name].zone_type == ZoneType.PRIORITY:
                cost -= 0.1
            elif self.map.zones[zone_name].zone_type == ZoneType.RESTRICTED:
                cost += 1.
        return cost

    def _assign_drones(self) -> None:
        for drone_id in range(1, self.map.nb_drones + 1):
            best_path = self.paths[0]
            self.drone_assignments[drone_id] = best_path[0]
            self.paths[0] = (best_path[0], best_path[1] + 1.)
            self.paths = sorted(self.paths, key=lambda p: p[1])

    def _schedule_drones(self) -> None:
        if not self.paths or not self.drone_assignments:
            return

        nb_drones = self.map.nb_drones
        steps: dict[int, int] = {d_id: 0 for d_id in range(1, nb_drones + 1)}
        waits: dict[int, int] = {d_id: 0 for d_id in range(1, nb_drones + 1)}
        delivered: set[int] = set()

        zone_count: dict[str, int] = {name: 0 for name in self.map.zones}
        zone_count[self.map.start_zone] = nb_drones

        delivered_res = set(range(1, nb_drones + 1))
        while delivered != delivered_res:
            turn_moves: list[tuple[int, str]] = []

            leaving: dict[str, int] = {name: 0 for name in self.map.zones}
            arriving: dict[str, int] = {name: 0 for name in self.map.zones}
            link_used: dict[tuple[str, str], int] = {}

            def is_zone_free(name: str) -> int:
                z = self.map.zones[name]
                net = zone_count[name] - leaving[name]
                return z.max_drones - net - arriving[name]

            def is_link_free(s: str, d: str) -> bool:
                node = self.graph.nodes.get(s)
                if not node:
                    return False

                edge = next((e for e in node.edges if e.to == d), None)
                cap = edge.capacity if edge else 1
                return link_used.get((s, d), 0) < cap

            for drone_id in range(1, nb_drones + 1):
                if drone_id in delivered:
                    continue

                path = self.drone_assignments[drone_id]
                step = steps[drone_id]

                if step == len(path) - 1:
                    delivered.add(drone_id)
                    continue
                if waits[drone_id] > 0:
                    waits[drone_id] -= 1
                    continue

                src = path[step]
                dst = path[step + 1]
                dst_zone = self.map.zones[dst]

                if not is_link_free(src, dst):
                    continue

                is_end = dst == self.map.end_zone
                if not is_end and is_zone_free(dst) <= 0:
                    continue

                leaving[src] += 1
                if not is_end:
                    arriving[dst] += 1
                link_used[(src, dst)] = link_used.get((src, dst), 0) + 1

                steps[drone_id] += 1
                turn_moves.append((drone_id, dst))

                if dst_zone.zone_type == ZoneType.RESTRICTED:
                    waits[drone_id] = 1

                if is_end:
                    delivered.add(drone_id)

            for name in self.map.zones:
                zone_count[name] += arriving[name] - leaving[name]

            if turn_moves:
                self.turns.append(turn_moves)

    @staticmethod
    def format_turn(turn: list[tuple[int, str]]) -> str:
        return " ".join(
            f"D{d_id}-{zone_name}" for d_id, zone_name in turn
            )
