from dataclasses import dataclass
from math import ceil, sqrt
from .Map import Map


@dataclass
class Rect:
    x: int
    y: int
    w: float
    h: float


class LayoutConfig:
    zone_padding: int = 20
    drone_padding: int = 5


@dataclass
class ZoneLayout:
    container: Rect
    center_x: int
    center_y: int
    radius: float
    drone_coords: list[tuple[int, int]]


@dataclass
class ConnectionLayout:
    start_x: int
    start_y: int
    end_x: int
    end_y: int


class MapLayout:
    def __init__(self, map_model: Map, cell_size: int = 48) -> None:
        self.map: Map = map_model
        self.cell_size: int = cell_size
        self.zone_layouts: dict[str, ZoneLayout] = {}
        self.connections_layouts: dict[tuple[str, str], ConnectionLayout] = {}

        self._init_zone_layouts()
        self._init_connection_layouts()

    def _init_zone_layouts(self) -> None:
        x = y = 0
        for name, zone in self.map.zones.items():
            cols = rows = ceil(sqrt(zone.max_drones))

            grid_w = (self.cell_size + LayoutConfig.drone_padding) * cols - LayoutConfig.drone_padding
            grid_h = (self.cell_size + LayoutConfig.drone_padding) * rows - LayoutConfig.drone_padding

            radius = sqrt((grid_w ** 2 + grid_h ** 2)) // 2 + LayoutConfig.drone_padding
            container = Rect(
                    x, y,
                    radius * 2 + LayoutConfig.zone_padding,
                    radius * 2 + LayoutConfig.zone_padding
                    )

            grid_x = (container.x + container.w - grid_w) // 2
            grid_y = (container.y + container.h - grid_w) // 2

            drone_coords: list[tuple[int, int]] = []
            count = 0
            for row in range(rows):
                for col in range(cols):
                    if count >= zone.max_drones:
                        break

                    drone_coords.append((
                        int(grid_x + col * (self.cell_size + LayoutConfig.drone_padding)),
                        int(grid_y + row * (self.cell_size + LayoutConfig.drone_padding))
                        ))

            zone_layout = ZoneLayout(
                    container,
                    int(radius + LayoutConfig.zone_padding),
                    int(radius + LayoutConfig.zone_padding),
                    radius,
                    drone_coords
                    )
            self.zone_layouts[name] = zone_layout

    def _init_connection_layouts(self) -> None:
        for name1, name2 in self.map.connections:
            zone1 = self.zone_layouts[name1]
            zone2 = self.zone_layouts[name2]

            m = (zone2.center_y - zone1.center_y) / (zone2.center_y - zone1.center_y)
            b = zone1.center_y - m * zone1.center_x
            y = lambda x: m * x + b

            start_x = int(zone1.center_x + zone1.radius / (sqrt(1 + m ** 2)))
            start_y = int(y(start_x))
            end_x = int(zone2.center_x - zone2.radius / (sqrt(1 + m ** 2)))
            end_y = int(y(end_x))

            self.connections_layouts[(name1, name2)] = ConnectionLayout(
                    start_x, start_y,
                    end_x, end_y
                    )
