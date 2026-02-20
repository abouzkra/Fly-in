import sys
from models import Map, ParsingError, ZoneType
import heapq
from typing import List

ZONE_COST = {
    'normal': 1,
    'priority': 1,
    'restricted': 2,
    'blocked': float('inf')
}

class Path:
    def __init__(self, zones: List[str], total_cost: int):
        self.zones = zones
        self.total_cost = total_cost
        self.assigned_drones = 0

def dijkstra(map_obj: 'Map', start: str, end: str) -> Path | None:
    """
    Compute the shortest path from start to end on the map considering zone types.
    Returns a Path object or None if no path exists.
    """
    heap = [(0, 0, start, [start])]
    visited = {}

    while heap:
        cost, neg_priority, current, path = heapq.heappop(heap)
        priority_count = -neg_priority

        if current == end:
            return Path(path, cost)

        if current in visited:
            prev_cost, prev_priority = visited[current]
            if cost > prev_cost or (cost == prev_cost and priority_count <= prev_priority):
                continue

        visited[current] = (cost, priority_count)

        zone = map_obj.zones[current]

        if zone.zone_type == ZoneType.BLOCKED:
            continue

        for neighbor in zone.neighbors:
            neighbor_zone = map_obj.zones[neighbor.name]

            if neighbor_zone.zone_type == ZoneType.BLOCKED:
                continue

            move_cost = ZONE_COST[neighbor_zone.zone_type.value]
            total_cost = cost + move_cost

            new_priority_count = priority_count
            if neighbor_zone.zone_type == ZoneType.PRIORITY:
                new_priority_count += 1

            heapq.heappush(heap, (total_cost, -new_priority_count, neighbor.name, path + [neighbor.name]))

    return None


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]

    try:
        m = Map()
        
        m.parse_file(file)

        path = dijkstra(m, m.start_zone, m.end_zone)
        if path:
            print("Shortest path:", path.zones)
            print("Total cost:", path.total_cost)
        else:
            print("No path found!")

        print("Map parsed successfully!")
    except ParsingError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
