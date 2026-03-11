from ..parser.map import Map
from ..parser.zone import ZoneType
from .graph import Graph


Path = list[str]
PathWithCost = tuple[Path, float]


class Solver:
    """Solver for the drone routing problem. It works in three steps:
    1. Find all valid paths from the start zone to the end zone, and compute
       their costs.
    2. Assign drones to paths, prioritizing cheaper paths.
    3. Schedule drone movements turn by turn, ensuring that zone and link
       capacities are respected.

    Attributes:
        map: The parsed map of the problem.
        graph: A graph representation of the map for pathfinding.
        paths: A list of valid paths from start to end, along with their costs.
        drone_assignments: A mapping of drone IDs to their assigned paths.
        turns: A list of turns, where each turn is a list of drone movements.
    """
    def __init__(self, parsed_map: Map) -> None:
        """Initialize the solver with the parsed map.

        Args:
            parsed_map: The map of the problem, containing zones, edges,
                and drone information.
        """
        self.map: Map = parsed_map
        self.graph: Graph = Graph(parsed_map)
        self.paths: list[PathWithCost] = []
        self.drone_assignments: dict[int, Path] = {}
        self.turns: list[list[tuple[int, str]]] = []

    def solve(self) -> None:
        """Solve the drone routing problem by executing the three main steps.

        Raises:
            Exception: If no valid paths are found from the start zone to the
                end
        """
        self._find_all_paths()
        if not self.paths:
            raise Exception(
                "Map has no valid paths from " +
                f"'{self.map.start_zone}' to '{self.map.end_zone}'"
                )
        self._assign_drones()
        self._schedule_drones()

    def _find_all_paths(self) -> None:
        """Runs BFS to find all valid paths from the start zone to the end
        zone, and computes their costs based on path length and zone types.

        Valid paths are those that do not pass through blocked zones and
        respect the map's structure. The results are stored in the `paths`
        attribute, sorted by cost.

        Only the two cheapest paths are kept for assignment, as the solver
        prioritizes efficiency and simplicity in drone assignments.
        """
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

        self.paths = sorted(res, key=lambda p: p[1])[0: 2]

    def _path_cost(self, path: Path) -> float:
        """Simple cost function that computes the cost of a path based on its
        length and the types of zones it passes through.
            - Priority zones reduce cost so they are favored.
            - Restricted zones increase cost to discourage their use.
            - Blocked zones are not considered valid paths and would have an
              infinite cost.
        """
        cost = 0.
        cost += len(path)

        for zone_name in path:
            if self.map.zones[zone_name].zone_type == ZoneType.PRIORITY:
                cost -= 0.1
            elif self.map.zones[zone_name].zone_type == ZoneType.RESTRICTED:
                cost += 1.
        return cost

    def _assign_drones(self) -> None:
        """Simple drone assignment strategy that assigns drones to the
        cheapest path first.
        """
        for drone_id in range(1, self.map.nb_drones + 1):
            best_path = self.paths[0]
            self.drone_assignments[drone_id] = best_path[0]
            self.paths[0] = (best_path[0], best_path[1] + 1.)
            self.paths = sorted(self.paths, key=lambda p: p[1])

    def _schedule_drones(self) -> None:
        """Schedules drone movements turn by turn, ensuring that zone and link
        capacities are respected. Drones move along their assigned paths, and
        the solver checks for conflicts at each turn, such as multiple drones
        trying to enter the same zone or use the same link. If a conflict is
        detected, the drone will wait until the next turn to attempt the move
        again. The results are stored in the `turns` attribute, which contains
        the sequence of drone movements for each turn."""
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
                """Checks whether a zone has free capacity for incoming drones,
                considering the current number of drones in the zone, the
                number of drones leaving, and the number of drones arriving.

                Args:
                    name: The name of the zone to check.

                Returns:
                    The number of free slots available in the zone for incoming
                    drones. A value of 0 or less indicates that the zone is at
                    or over capacity, while a positive value indicates the
                    number of additional drones that can enter the zone without
                    exceeding its capacity.
                """
                z = self.map.zones[name]
                net = zone_count[name] - leaving[name]
                return z.max_drones - net - arriving[name]

            def is_link_free(s: str, d: str) -> bool:
                """Checks whether a link between two zones has free capacity
                for drones to use, considering the number of drones currently
                using the link.

                Args:
                    s: The source zone of the link.
                    d: The destination zone of the link.

                Returns:
                    True if the link has free capacity for another drone to
                    use, False if the link is at or over capacity.
                """
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
        """Stringifies a turn, which is a list of drone movements, into the
        required output format.

        Args:
            turn: A list of tuples, where each tuple contains a drone ID and
                the zone it moves to in that turn.
        """
        return " ".join(
            f"D{d_id}-{zone_name}" for d_id, zone_name in turn
            )
