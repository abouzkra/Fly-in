from math import sqrt
from pyray import *


class RenderDrone:
    SPEED = 200.0

    def __init__(self, drone_id: int, zone: str, slot_key, x: int, y: int):
        self.id = drone_id
        self.zone = zone

        self.current_slot = slot_key
        self.target_slot = None

        self.x = float(x)
        self.y = float(y)

        self.is_moving = False
        self.phase = 0

        self.connection = None
        self.texture = None

        self.start_x = 0.0
        self.start_y = 0.0
        self.end_x = 0.0
        self.end_y = 0.0

    def start_turn(self, connection, target_slot_key, target_slot_pos, texture):
        self.connection = connection
        self.target_slot = target_slot_key
        self.texture = texture

        self.phase = 0
        self.is_moving = True

        self.start_x = self.x
        self.start_y = self.y

        self.end_x = connection.start_x - texture.width // 2
        self.end_y = connection.start_y - texture.height // 2

    def update(self):
        if not self.is_moving:
            return

        finished = self._move_step()

        if not finished:
            return

        if self.phase == 0:
            self.phase = 1
            self.start_x = self.x
            self.start_y = self.y
            self.end_x = self.connection.end_x - self.texture.width // 2
            self.end_y = self.connection.end_y - self.texture.height // 2

        elif self.phase == 1:
            self.phase = 2
            self.start_x = self.x
            self.start_y = self.y
            self.end_x, self.end_y = self.target_slot[1]

        elif self.phase == 2:
            self.is_moving = False
            self.phase = 3

    def _move_step(self) -> bool:
        dx = self.end_x - self.x
        dy = self.end_y - self.y

        dist = sqrt(dx * dx + dy * dy)

        if dist < 2:
            self.x = self.end_x
            self.y = self.end_y
            return True

        norm_dx = dx / dist
        norm_dy = dy / dist

        step = self.SPEED * get_frame_time()

        self.x += norm_dx * step
        self.y += norm_dy * step

        return False


class MapRenderer:
    def __init__(self, layout, drone_texture):
        self.layout = layout
        self.drone_texture = drone_texture

        self.drones: dict[int, RenderDrone] = {}

        self.turns = []
        self.current_turn = 0
        self.playing = False

        start_zone = layout.map.start_zone
        start_layout = layout.zone_layouts[start_zone]

        drone_id = 1
        for slot_key, occupied in start_layout.drone_coords.items():
            if not occupied:
                start_layout.drone_coords[slot_key] = True

                self.drones[drone_id] = RenderDrone(
                    drone_id,
                    start_zone,
                    slot_key,
                    slot_key[0],
                    slot_key[1],
                )

                drone_id += 1

    def load_turns(self, turns):
        self.turns = turns
        self.current_turn = 0
        self.playing = True

    def draw(self):
        self._update()

        for connection in self.layout.connections_layouts.values():
            draw_line_ex(
                (connection.start_x, connection.start_y),
                (connection.end_x, connection.end_y),
                3.0,
                BLACK,
            )

        for zone_layout in self.layout.zone_layouts.values():
            draw_circle(
                zone_layout.center_x,
                zone_layout.center_y,
                zone_layout.radius,
                LIGHTGRAY,
            )

        for drone in self.drones.values():
            draw_texture(
                self.drone_texture,
                int(drone.x),
                int(drone.y),
                WHITE,
            )

    def _update(self):
        for drone in self.drones.values():
            drone.update()

        if self.playing and all(not d.is_moving for d in self.drones.values()):
            if self.current_turn < len(self.turns):
                print(self.turns[self.current_turn])
                self._start_turn(self.turns[self.current_turn])
                self.current_turn += 1
            else:
                self.playing = False

    def _start_turn(self, turn):
        for drone_id, next_zone in turn:
            drone = self.drones[drone_id]

            if drone.is_moving:
                continue

            from_zone = drone.zone
            connection = self.layout.connections_layouts[(from_zone, next_zone)]

            target_layout = self.layout.zone_layouts[next_zone]
            free_slot = None

            for slot_key, occupied in target_layout.drone_coords.items():
                if not occupied:
                    free_slot = slot_key
                    break

            if free_slot is None:
                continue

            target_layout.drone_coords[free_slot] = True

            self.layout.zone_layouts[from_zone].drone_coords[
                drone.current_slot
            ] = False

            drone.start_turn(
                connection,
                (next_zone, free_slot),
                free_slot,
                self.drone_texture,
            )

            drone.zone = next_zone
            drone.current_slot = free_slot
