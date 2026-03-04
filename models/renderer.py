from math import sqrt
from pyray import *
from .layout import ConnectionLayout, MapLayout


class RenderDrone:
    SPEED: float = 300.0

    def __init__(
            self,
            drone_id: int,
            start_zone: str,
            x: int, y: int
            ) -> None:
        self.id: int = drone_id
        self.from_zone: str = start_zone

        self.connection: ConnectionLayout | None = None

        self.current_slot: tuple[int, int] = (x, y)
        self.target_slot: tuple[int, int] = (x, y)

        self.x: float = float(x)
        self.y: float = float(y)

        self.is_moving: bool = False
        self.phase: int = 0

        self.start_x: float = 0.0
        self.start_y: float = 0.0
        self.end_x: float = 0.0
        self.end_y: float = 0.0

    def start_move(
            self,
            connection: ConnectionLayout,
            target_slot: tuple[int, int],
            tex_half_w: int, tex_half_h: int
            ) -> None:
        self.connection = connection
        self.target_slot = target_slot

        self.phase = 0
        self.is_moving = True

        self.start_x = self.x
        self.start_y = self.y

        self.end_x = connection.start_x - tex_half_w
        self.end_y = connection.start_y - tex_half_h

    def update(self, tex_half_w: int, tex_half_h: int) -> None:
        if not self.is_moving or not self._move():
            return

        if self.phase == 0:
            self.phase = 1
            self.start_x = self.x
            self.start_y = self.y
            self.end_x = self.connection.end_x - tex_half_w
            self.end_y = self.connection.end_y - tex_half_h
        elif self.phase == 1:
            self.phase = 2
            self.start_x = self.x
            self.start_y = self.y
            self.end_x, self.end_y = self.target_slot
        elif self.phase == 2:
            self.phase = 3
            self.is_moving = False

    def _move(self) -> bool:
        dx = self.end_x - self.x
        dy = self.end_y - self.y

        dist = dx ** 2 + dy ** 2
        step = 200 * get_frame_time()
        
        if dist < step * step:
            self.x = self.end_x 
            self.y = self.end_y
            return True

        dist = sqrt(dist)
        norm_dx = dx / dist
        norm_dy = dy / dist

        self.x += norm_dx * step
        self.y += norm_dy * step

        return False


class MapRenderer:
    def __init__(self, layout: MapLayout, drone_texture: Texture):
        self.layout: MapLayout = layout
        self.drone_texture: Texture = drone_texture
        self.tex_half_w: int = drone_texture.width // 2
        self.tex_half_h: int = drone_texture.height // 2

        self.drones: dict[int, RenderDrone] = {}

        self.turns: list[list[tuple[int, str]]] = []
        self.current_turn: int = 0
        self.playing: bool = False

        start_zone = layout.map.start_zone
        start_layout = layout.zone_layouts[start_zone]
        drone_id = 1
        for key, occupied in start_layout.drone_coords.items():
            if not occupied:
                start_layout.drone_coords[key] = True
                self.drones[drone_id] = RenderDrone(
                        drone_id,
                        start_zone,
                        key[0], key[1]
                        )
                drone_id += 1

    def load_turns(self, turns: list[list[tuple[int, str]]]) -> None:
        self.turns = turns
        self.playing = True

    def draw(self) -> None:
        self._update()

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
                    WHITE
                    )
            draw_circle_lines(
                    zone_layout.center_x,
                    zone_layout.center_y,
                    zone_layout.radius,
                    LIGHTGRAY
                    )

        for drone in self.drones.values():
            text = str(drone.id)
            font_size = 12
            text_w = measure_text(text, font_size)

            draw_texture(
                self.drone_texture,
                int(drone.x), int(drone.y),
                BLACK
                )
            draw_text(
                text,
                int(drone.x + self.tex_half_w - text_w // 2),
                int(drone.y + self.tex_half_h - font_size // 2),
                font_size,
                WHITE
                )
            
    def _update(self) -> None:
        for drone in self.drones.values():
            drone.update(self.tex_half_w, self.tex_half_h)

        turn_anim_ended = all(not d.is_moving for d in self.drones.values())
        if self.playing and turn_anim_ended:
            if self.current_turn < len(self.turns):
                self._start_turn(self.current_turn)
                self.current_turn += 1
            else:
                self.playing = False

    def _start_turn(self, turn_idx: int) -> None:
        for drone_id, next_zone in self.turns[turn_idx]:
            drone = self.drones[drone_id]
            if drone.is_moving:
                continue

            connection = self.layout.connections_layouts[
                    (drone.from_zone, next_zone)
                    ]
            target_layout = self.layout.zone_layouts[next_zone]
            free_slot = None

            for slot, occupied in target_layout.drone_coords.items():
                if not occupied:
                    free_slot = slot
                    break

            if not free_slot:
                continue

            target_layout.drone_coords[free_slot] = True
            self.layout.zone_layouts[drone.from_zone].drone_coords[
                drone.current_slot
                ] = False

            drone.start_move(
                connection,
                free_slot,
                self.tex_half_w,
                self.tex_half_h
                )

            drone.from_zone = next_zone
            drone.current_slot = free_slot
