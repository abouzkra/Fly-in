from Map import Map
from zone import ZoneType
from graph import Graph


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
        capacities are respected, drones move along their assigned paths, and
        the solver checks for conflicts at each turn. If a conflict is
        is detected, the drone will wait until permitted to move.
        """
        if not self.paths or not self.drone_assignments:
            return

        nb_drones = self.map.nb_drones
        steps: dict[int, int] = {d_id: 0 for d_id in range(1, nb_drones + 1)}
        waits: dict[int, int] = {d_id: 0 for d_id in range(1, nb_drones + 1)}
        delivered: set[int] = set()
        delivered_res = set(range(1, nb_drones + 1))

        while delivered != delivered_res:
            turn_moves: list[tuple[int, str]] = []
            self.graph.reset()

            for drone_id in range(1, nb_drones + 1):
                if drone_id in delivered:
                    continue

                path = self.drone_assignments[drone_id]
                step = steps[drone_id]

                src_node = self.graph.nodes[path[step]]
                dst_node = self.graph.nodes[path[step + 1]]
                dst_zone = self.map.zones[path[step + 1]]

                if waits[drone_id] > 0:
                    waits[drone_id] -= 1
                    turn_moves.append((drone_id, src_node.name))
                    continue

                edge = src_node.get_edge(dst_node.name)
                is_end = dst_node.name == self.map.end_zone
                if (
                    (not is_end and dst_node.free_capacity() <= 0)
                    or (edge is None or not edge.is_free())
                ):
                    continue

                src_node.leaving += 1
                if not is_end:
                    dst_node.arriving += 1
                edge.used += 1
                steps[drone_id] += 1
                if dst_zone.zone_type == ZoneType.RESTRICTED:
                    turn_moves.append(
                        (drone_id, f"{src_node.name}-{dst_node.name}")
                        )
                    waits[drone_id] = 1
                else:
                    turn_moves.append((drone_id, dst_node.name))

                if is_end:
                    delivered.add(drone_id)

            self.graph.commit_turn()
            self.turns.append(turn_moves)

    def format_turn(self, turn_idx: int) -> str:
        """Stringifies a turn, which is a list of drone movements, into the
        required output format.

        Args:
            turn: A list of tuples, where each tuple contains a drone ID and
                the zone it moves to in that turn.
        """
        turn = self.turns[turn_idx]
        return " ".join(
            f"D{d_id}-{zone_name}" for d_id, zone_name in turn
            )
