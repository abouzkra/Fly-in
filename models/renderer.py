from pyray import *
from raylib import MeasureText
from .layout import ConnectionLayout, LayoutConfig, MapLayout, ZoneLayout


class MapRenderer:
    def __init__(self, layout: MapLayout, drone_texture: Texture):
        self.layout: MapLayout = layout
        self.drone_texture: Texture = drone_texture

    def draw(self) -> None:
        for connection_layout in self.layout.connections_layouts.values():
            self._draw_connection(connection_layout)

        for name, zone_layout in self.layout.zone_layouts.items():
            self._draw_zone(name, zone_layout)

    def animate_turns(self, turns: list[list[tuple[int, str]]]) -> None:
        pass

    def _draw_zone(self, name: str, zone_layout: ZoneLayout) -> None:
        draw_circle(
                zone_layout.center_x,
                zone_layout.center_y,
                zone_layout.radius,
                LIGHTGRAY
                )

    def _draw_connection(self, connection_layout: ConnectionLayout) -> None:
        draw_line_ex(
            (connection_layout.start_x, connection_layout.start_y),
            (connection_layout.end_x, connection_layout.end_y),
            3.0,
            BLACK
            )
