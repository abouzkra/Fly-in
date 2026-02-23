from pyray import Texture

from .layout import MapLayout


class MapRenderer:
    def __init__(self, layout: MapLayout, drone_texture: Texture):
        self.layout: MapLayout = layout
        self.drone_texture: Texture = drone_texture

    def draw(self) -> None:
        pass
