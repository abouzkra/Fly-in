from math import sqrt
from pyray import *
from .layout import MapLayout


class RenderDrone:
    def __init__(self, drone_id: int, start_zone: str, x: int, y: int) -> None:
        self.id: int = drone_id
        self.from_zone: str = start_zone
        self.to_zone: str = ""
        self.x: float = x
        self.y: float = y
        self.is_moving: bool = False
        self.start_x: float = 0.0
        self.start_y: float = 0.0
        self.end_x: float = 0.0
        self.end_y: float = 0.0
        self.phase: int = 0


class MapRenderer:
    def __init__(self, layout: MapLayout, drone_texture: Texture):
        self.layout: MapLayout = layout
        self.drone_texture: Texture = drone_texture
        self.drones: dict[int, RenderDrone] = {}

        start_hub_layout = layout.zone_layouts['start']
        count = 1
        for (x, y), _ in start_hub_layout.drone_coords.items():
            self.drones[count] = RenderDrone(count, 'start',x , y)
            count += 1

    def draw(self) -> None:
        for connection_layout in self.layout.connections_layouts.values():
            draw_line_ex(
                (connection_layout.start_x, connection_layout.start_y),
                (connection_layout.end_x, connection_layout.end_y),
                3.0,
                BLACK
                )

        for _, zone_layout in self.layout.zone_layouts.items():
            draw_circle(
                    zone_layout.center_x,
                    zone_layout.center_y,
                    zone_layout.radius,
                    LIGHTGRAY
                    )

        for drone in self.drones.values():
            draw_texture(
                self.drone_texture,
                int(drone.x), int(drone.y),
                BLACK
                )

        self._drone_movement_simulation()

    def _drone_movement_simulation(self) -> None:
        def move(drone: RenderDrone, next_x: int, next_y: int) -> bool:
            dx = next_x - drone.x
            dy = next_y - drone.y

            dist = sqrt(dx ** 2 + dy ** 2)
            
            if drone.x > next_x or drone.y > next_y:
                drone.x = next_x
                drone.y = next_y
                return True

            norm_dx = dx / dist
            norm_dy = dy / dist

            step = 20 * get_frame_time()

            drone.x += norm_dx * step
            drone.y += norm_dy * step

            return False

        drone = self.drones[7]
        connection = self.layout.connections_layouts[('start', 'gate1')]

        # # move drone to start of connection
        # move(drone, connection.start_x, connection.start_y)
        #
        # # move drone to end of connection
        # move(drone, connection.end_x, connection.end_y)
        # # move drone to pos inside next_zone
        #
        # next_x, next_y = list(self.layout.zone_layouts['gate1'].drone_coords)[0]
        # move(drone, next_x, next_y)

        if drone.phase == 0:
            if move(drone, connection.start_x - self.drone_texture.width // 2, connection.start_y - self.drone_texture.height// 2):
                drone.phase = 1

        elif drone.phase == 1:
            if move(drone, connection.end_x - self.drone_texture.width // 2, connection.end_y - self.drone_texture.height// 2):
                drone.phase = 2

        elif drone.phase == 2:
            next_x, next_y = list(
                self.layout.zone_layouts['gate1'].drone_coords
            )[0]

            if move(drone, next_x, next_y):
                drone.phase = 3
