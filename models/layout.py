from dataclasses import dataclass
from math import ceil, sqrt
from pyray import Rectangle
from .map import Map


class LayoutConfig:
    zone_x_padding: int = 20
    zone_y_padding: int = 50
    drone_padding: int = 5


@dataclass
class ZoneLayout:
    container: Rectangle
    col: int
    row: int
    center_x: int
    center_y: int
    radius: float
    drone_coords: dict[tuple[int, int], bool]
    color: int


@dataclass
class ConnectionLayout:
    start_x: int
    start_y: int
    end_x: int
    end_y: int


@dataclass
class PanelLayout:
    container: Rectangle
    turn_info: Rectangle
    buttons: dict[str, Rectangle]


class MapLayout:
    def __init__(self, map_model: Map, cell_size: int = 48) -> None:
        self.map: Map = map_model
        self.cell_size: int = cell_size
        self.zone_layouts: dict[str, ZoneLayout] = {}
        self.connections_layouts: dict[tuple[str, str], ConnectionLayout] = {}
        self.panel_layout: PanelLayout | None = None

        self._init_zone_layouts()
        self._init_connection_layouts()
        self._init_panel_layout()

    def _init_zone_layouts(self) -> None:
        min_x = min(zone.x for zone in self.map.zones.values())
        min_y = min(zone.y for zone in self.map.zones.values())

        container_sizes: dict[str, tuple[float, float, float]] = {}
        zone_grid: dict[str, tuple[int, int, int, int]] = {}

        container_x: int = 0
        container_y: int = 0
        for name, zone in self.map.zones.items():
            col, row = zone.x - min_x, zone.y - min_y

            cols = rows = ceil(sqrt(zone.max_drones))

            grid_w = (self.cell_size + LayoutConfig.drone_padding) \
                * cols - LayoutConfig.drone_padding
            grid_h = (self.cell_size + LayoutConfig.drone_padding) \
                * rows - LayoutConfig.drone_padding

            radius = sqrt((grid_w ** 2 + grid_h ** 2)) // 2 + \
                LayoutConfig.drone_padding

            container_sizes[name] = (
                    radius * 2 + LayoutConfig.zone_x_padding,
                    radius * 2 + LayoutConfig.zone_y_padding,
                    radius
                    )
            zone_grid[name] = (zone.x - min_x, zone.y - min_y, grid_w, grid_h)

        col_widths = {}
        row_heights = {}
        for name, (col, row, _, __) in zone_grid.items():
            w, h, r = container_sizes[name]

            col_widths[col] = max(col_widths.get(col, 0), w)
            row_heights[row] = max(row_heights.get(row, 0), h)

        col_offsets = {}
        row_offsets = {}

        current = 0
        for col in sorted(col_widths):
            col_offsets[col] = current
            current += col_widths[col]
        current = 0
        for row in sorted(row_heights):
            row_offsets[row] = current
            current += row_heights[row]

        for name, (col, row, grid_w, grid_h) in zone_grid.items():
            w, h, radius = container_sizes[name]

            w, h = col_widths[col], row_heights[row]
            container_x, container_y = col_offsets[col], row_offsets[row]
            container = Rectangle(container_x, container_y, w, h)

            center_x = container_x + w // 2
            center_y = container_y + h // 2

            zone = self.map.zones[name]
            cols = rows = ceil(sqrt(zone.max_drones))

            grid_x = container.x + (container.width - grid_w) // 2
            grid_y = container.y + (container.height - grid_h) // 2

            drone_coords: dict[tuple[int, int], bool] = {}
            count = 0
            for r in range(rows):
                for c in range(cols):
                    if count >= zone.max_drones:
                        break
                    x = int(grid_x + c * (self.cell_size +
                                          LayoutConfig.drone_padding))
                    y = int(grid_y + r * (self.cell_size +
                                          LayoutConfig.drone_padding))
                    drone_coords[(x, y)] = False
                    count += 1

            self.zone_layouts[name] = ZoneLayout(
                container,
                col, row,
                int(center_x), int(center_y),
                radius,
                drone_coords,
                zone.color
                )

    def _init_connection_layouts(self) -> None:
        for name1, name2 in self.map.connections:
            zone1 = self.zone_layouts[name1]
            zone2 = self.zone_layouts[name2]

            dx = zone2.center_x - zone1.center_x
            dy = zone2.center_y - zone1.center_y

            length = sqrt(dx ** 2 + dy ** 2)

            if length == 0:
                continue

            # Vector normalization
            norm_dx = dx / length
            norm_dy = dy / length

            start_x = zone1.center_x + norm_dx * zone1.radius
            start_y = zone1.center_y + norm_dy * zone1.radius
            end_x = zone2.center_x - norm_dx * zone2.radius
            end_y = zone2.center_y - norm_dy * zone2.radius

            self.connections_layouts[(name1, name2)] = ConnectionLayout(
                    int(start_x), int(start_y),
                    int(end_x), int(end_y)
                    )

    def _init_panel_layout(self) -> None:
        total_w = int(max(
            layout.container.x + layout.container.width
            for layout in self.zone_layouts.values()
            ))
        map_h = int(max(
            layout.container.y + layout.container.height
            for layout in self.zone_layouts.values()
            ))
        panel_w = 500 if total_w < 500 else total_w
        panel_h = 55
        container = Rectangle(
                0, map_h,
                panel_w,
                panel_h
                )

        turn_info = Rectangle(
                container.x,
                container.y,
                container.width / 4,
                container.height
                )

        buttons: dict[str, Rectangle] = {}
        x = turn_info.x + turn_info.width
        for btn in ('play_pause', 'step', 'restart'):
            buttons[btn] = Rectangle(
                x, turn_info.y,
                turn_info.width,
                turn_info.height
                )
            x += turn_info.width

        self.panel_layout = PanelLayout(
                container,
                turn_info,
                buttons
                )
