from math import sqrt
from pyray import (
        BLACK, BLUE, GREEN, ORANGE, RED, VIOLET, WHITE, YELLOW, Color, Texture,
        draw_circle, draw_line_ex, draw_text, draw_texture, get_color,
        get_frame_time, measure_text, gui_button
        )
from solver import Solver
from layout import ConnectionLayout, MapLayout


class RenderDrone:
    """Represents a drone in the renderer, handling its position and movement
    animation.

    Attributes:
        id (int): Unique identifier for the drone.
        from_zone (str): The zone from which the drone is moving.
        connection (ConnectionLayout): The connection layout the drone is
            currently moving along.
        current_slot (tuple[int, int]): The current slot coordinates of the
            drone in its zone.
        target_slot (tuple[int, int]): The target slot coordinates of the
            drone in its destination zone.
        x (float): The current x-coordinate of the drone for rendering.
        y (float): The current y-coordinate of the drone for rendering.
        is_moving (bool): Indicates whether the drone is currently moving.
        phase (int): The current phase of the movement animation (
            0: moving to connection start,
            1: moving along connection,
            2: moving to target slot
            ).
        start_x (float): The starting x-coordinate for the current movement
            phase.
        start_y (float): The starting y-coordinate for the current movement
            phase.
        end_x (float): The ending x-coordinate for the current movement phase.
        end_y (float): The ending y-coordinate for the current movement phase.
    """
    def __init__(
            self,
            drone_id: int,
            start_zone: str,
            x: int, y: int
            ) -> None:
        self.id: int = drone_id
        self.from_zone: str = start_zone

        self.connection: ConnectionLayout

        self.current_slot: tuple[int, int] = (x, y)
        self.target_slot: tuple[int, int] = (x, y)

        self.x: float = float(x)
        self.y: float = float(y)

        self.is_moving: bool = False
        self.is_transit: bool = False
        self.phase: int = 0

        self.start_x: float = 0.0
        self.start_y: float = 0.0
        self.end_x: float = 0.0
        self.end_y: float = 0.0

    def start_transit(
            self,
            connection: ConnectionLayout,
            tex_half_w: int,
            tex_half_h: int
            ) -> None:
        """Animate the drone from its current slot to the midpoint of the
        connection, then stop there. Called when a restricted transit begins.

        Two phases:
            0: current slot -> connection start point
            1: connection start -> connection midpoint  (stop here)
        """
        self.connection = connection
        self.phase = 0
        self.is_moving = True

        self.start_x = self.x
        self.start_y = self.y
        self.end_x = connection.start_x - tex_half_w
        self.end_y = connection.start_y - tex_half_h

    def start_arrival(
            self,
            connection: ConnectionLayout,
            target_slot: tuple[int, int],
            tex_half_w: int,
            tex_half_h: int
            ) -> None:
        """Animate the drone from the connection midpoint to the destination
        slot. Called the turn after start_transit, when the drone must arrive.

        Two phases:
            0: connection midpoint -> connection end point
            1: connection end -> target slot
        """
        self.connection = connection
        self.target_slot = target_slot
        self.phase = 3
        self.is_moving = True
        self.is_transit = False

        self.start_x = self.x
        self.start_y = self.y
        self.end_x = connection.end_x - tex_half_w
        self.end_y = connection.end_y - tex_half_h

    def start_move(
            self,
            connection: ConnectionLayout,
            target_slot: tuple[int, int],
            tex_half_w: int, tex_half_h: int
            ) -> None:
        """Iinitiates the movement of the drone along a connection towards a
        target slot.

        Args:
            connection (ConnectionLayout): The connection layout the drone
                will move along.
            target_slot (tuple[int, int]): The target slot coordinates in the
                destination zone.
            tex_half_w (int): Half the width of the drone texture, used for
                centering the drone during movement.
            tex_half_h (int): Half the height of the drone texture, used for
                centering the drone during movement.
        """
        self.connection = connection
        self.target_slot = target_slot
        self.phase = 0
        self.is_moving = True

        self.start_x = self.x
        self.start_y = self.y
        self.end_x = connection.start_x - tex_half_w
        self.end_y = connection.start_y - tex_half_h

    def update(self, tex_half_w: int, tex_half_h: int) -> None:
        """Updates the drone's position based on its current movement phase and
        the elapsed time.

        Args:
            tex_half_w (int): Half the width of the drone texture, used for
                centering the drone during movement.
            tex_half_h (int): Half the height of the drone texture, used for
                centering the drone during movement.
        """

        if not self.is_moving or not self._move():
            return

        mid_x = (self.connection.start_x + self.connection.end_x) // 2
        mid_y = (self.connection.start_y + self.connection.end_y) // 2

        if self.phase == 0:
            self.phase = 1
            self.start_x = self.x
            self.start_y = self.y
            if self.is_transit:
                self.end_x = mid_x - tex_half_w
                self.end_y = mid_y - tex_half_h
            else:
                self.end_x = self.connection.end_x - tex_half_w
                self.end_y = self.connection.end_y - tex_half_h

        elif self.phase == 1:
            if self.is_transit:
                self.is_moving = False
            else:
                self.phase = 2
                self.start_x = self.x
                self.start_y = self.y
                self.end_x, self.end_y = self.target_slot

        elif self.phase == 2:
            self.phase = 3
            self.is_moving = False

        elif self.phase == 3:
            self.phase = 4
            self.start_x = self.x
            self.start_y = self.y
            self.end_x, self.end_y = self.target_slot

        elif self.phase == 4:
            self.phase = 5
            self.is_moving = False

    def _move(self) -> bool:
        """Moves the drone towards its current target position based on the
        elapsed time and returns whether it has reached the target."""
        SPEED = 300.0
        dx = self.end_x - self.x
        dy = self.end_y - self.y

        dist = dx ** 2 + dy ** 2
        step = SPEED * get_frame_time()

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
    """Holds all the rendering logic for the map, including drawing the map
    layout, drones, and handling the animation of drone movements and user
    interactions.

    Attributes:
        layout (MapLayout): The layout of the map, including zones and
            connections.
        solver (Solver): The solver instance which contains turns.
        drone_texture (Texture): The texture used to represent drones on the
            map.
        tex_half_w (int): Half the width of the drone texture, used for
            centering drones during movement.
        tex_half_h (int): Half the height of the drone texture, used for
            centering drones during movement.
        drones (dict[int, RenderDrone]): A dictionary mapping drone IDs to
            their corresponding RenderDrone instances.
        turns (list[list[tuple[int, str]]]): A list of turns, where each turn
            is a list of tuples containing drone ID and the next zone it will
            move to.
        current_turn (int): The index of the current turn being displayed.
        playing (bool): Indicates whether the animation is currently playing.
        _initial_drone_coords (dict[str, dict[tuple[int, int], bool]]): A
            dictionary storing the initial coordinates of drones in each zone,
            used for resetting the map when restarting the animation.
        buttons (dict[str, int]): A dictionary mapping button labels to their
            corresponding GUI elements.
    """
    def __init__(self, layout: MapLayout, drone_texture: Texture,
                 solver: Solver):
        """Initializes the MapRenderer with the given map layout and drone
        texture.

        Args:
            layout (MapLayout): The layout of the map, including zones and
                connections.
            solver (Solver): The solver instance which contains turns.
            drone_texture (Texture): The texture used to represent drones on
                the map.
        """
        self.layout: MapLayout = layout
        self.solver: Solver = solver
        self.drone_texture: Texture = drone_texture
        self.tex_half_w: int = drone_texture.width // 2
        self.tex_half_h: int = drone_texture.height // 2

        self.drones: dict[int, RenderDrone] = {}

        self.current_turn: int = 0
        self.playing: bool = False

        self._initial_drone_coords: dict[str, dict[tuple[int, int], bool]] = {}
        self._spawn_drones()

        self.buttons: dict[str, int] = {}

    def draw_map(self) -> None:
        """Draws the map layout, including connections, zones, and drones, and
        updates the positions of moving drones."""
        self._update()

        for connection_layout in self.layout.connections_layouts.values():
            draw_line_ex(
                (connection_layout.start_x, connection_layout.start_y),
                (connection_layout.end_x, connection_layout.end_y),
                3.0,
                BLACK
                )

        for zone_layout in self.layout.zone_layouts.values():
            if zone_layout.color == -1:
                self._draw_rainbow_circle(
                    zone_layout.center_x,
                    zone_layout.center_y,
                    zone_layout.radius,
                    )
            else:
                draw_circle(
                    zone_layout.center_x,
                    zone_layout.center_y,
                    zone_layout.radius,
                    get_color(zone_layout.color)
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

    def draw_panel(self) -> None:
        """Draws the control panel, including the current turn information and
        control buttons."""
        panel = self.layout.panel_layout
        if not panel:
            return

        displayed_turns = 0
        if self.playing or self.current_turn > 0:
            displayed_turns = max(0, self.current_turn)
        text = f"Turn {displayed_turns} / {len(self.solver.turns)}"
        font_size = 20

        draw_text(
            text,
            int((panel.turn_info.x +
                 panel.turn_info.width -
                 measure_text(text, font_size)) // 2),
            int(panel.turn_info.y + (panel.turn_info.height - font_size) // 2),
            font_size,
            Color(0, 0, 0, 191)
            )

        btn_labels = {
            'play_pause': "#132#Pause" if self.playing else "#131#Play",
            'step': "#134#Next",
            'restart': "#77#Restart"
            }

        for btn, label in btn_labels.items():
            rect = panel.buttons[btn]
            self.buttons[btn] = gui_button(rect, label)

    def _draw_rainbow_circle(self, x: int, y: int, radius: float) -> None:
        """Draws a circle with rainbow colors, used for zones with 'rainbow'
        color value."""
        gradients = [
                RED, ORANGE, YELLOW, GREEN,
                BLUE, Color(75, 0, 130, 255), VIOLET
                ]
        r = radius
        for c in gradients:
            draw_circle(x, y, r, c)
            r -= radius / 7

    def handle_click(self) -> None:
        """Handles click events on the control panel."""
        panel = self.layout.panel_layout
        if not panel:
            return

        if not tuple(self.buttons) == ('play_pause', 'step', 'restart'):
            return

        if self.buttons['play_pause']:
            if (
                not self.playing
                and self.current_turn >= len(self.solver.turns)
            ):
                return
            self.playing = not self.playing
        if self.buttons['step']:
            self.playing = False
            all_idle = all(not d.is_moving for d in self.drones.values())

            if all_idle and self.current_turn < len(self.solver.turns):
                self._start_turn(self.current_turn)
                self.current_turn += 1
        if self.buttons['restart']:
            self._restart()

    def _spawn_drones(self) -> None:
        """Spawns drones in the starting zone based on the initial layout and
        stores their initial coordinates for resetting when restarting
        the animation."""
        start_zone = self.layout.map.start_zone
        start_layout = self.layout.zone_layouts[start_zone]
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

        self._initial_drone_coords = {
            name: dict(zl.drone_coords)
            for name, zl in self.layout.zone_layouts.items()
            }

    def _update(self) -> None:
        """Updates the positions of all moving drones and checks if the
        current turn's animation has ended:
            - If the animation has ended and the animation is playing, it
                starts the next turn.
            - Else, it continues updating the positions of the moving drones
            until they reach their targets.
        """
        for drone in self.drones.values():
            drone.update(self.tex_half_w, self.tex_half_h)

        turn_anim_ended = all(not d.is_moving for d in self.drones.values())
        if self.playing and turn_anim_ended:
            if self.current_turn < len(self.solver.turns):
                self._start_turn(self.current_turn)
                self.current_turn += 1
            else:
                self.playing = False

    def _start_turn(self, turn_idx: int) -> None:
        for drone_id, label in self.solver.turns[turn_idx]:
            drone = self.drones[drone_id]
            if drone.is_moving:
                continue

            is_transit_move = "-" in label

            if is_transit_move:
                src, dst = label.split("-", 1)
                connection = self.layout.connections_layouts.get((src, dst))
                assert connection is not None

                target_layout = self.layout.zone_layouts[dst]
                free_slot = next(
                    (s for s, occ in target_layout.drone_coords.items()
                     if not occ),
                    None
                )
                if not free_slot:
                    continue

                target_layout.drone_coords[free_slot] = True
                self.layout.zone_layouts[drone.from_zone].drone_coords[
                    drone.current_slot] = False

                drone.is_transit = True
                drone.target_slot = free_slot
                drone.current_slot = free_slot
                drone.start_transit(connection, self.tex_half_w,
                                    self.tex_half_h)
            elif drone.is_transit:
                next_zone = label
                connection = self.layout.connections_layouts.get(
                    (drone.from_zone, next_zone)
                )
                assert connection is not None

                drone.from_zone = next_zone
                drone.start_arrival(
                    connection,
                    drone.target_slot,
                    self.tex_half_w,
                    self.tex_half_h
                )
            else:
                next_zone = label
                connection = self.layout.connections_layouts.get(
                    (drone.from_zone, next_zone)
                )
                assert connection is not None

                target_layout = self.layout.zone_layouts[next_zone]
                free_slot = next(
                    (s for s, occ in target_layout.drone_coords.items()
                     if not occ),
                    None
                )
                if not free_slot:
                    continue

                target_layout.drone_coords[free_slot] = True
                self.layout.zone_layouts[drone.from_zone].drone_coords[
                    drone.current_slot] = False

                drone.start_move(
                    connection,
                    free_slot,
                    self.tex_half_w,
                    self.tex_half_h
                )
                drone.from_zone = next_zone
                drone.current_slot = free_slot

        print(self.solver.format_turn(turn_idx))

    def _restart(self) -> None:
        """Resets the map to its initial state by resetting the drone
        coordinates in each zone, clearing the current drones, respawning the
        drones in the starting zone, and resetting the current turn and
        playing state."""
        for name, coords in self._initial_drone_coords.items():
            zl = self.layout.zone_layouts[name]
            zl.drone_coords = dict(coords)

        for zl in self.layout.zone_layouts.values():
            for slot in zl.drone_coords:
                zl.drone_coords[slot] = False

        self.drones.clear()
        self._spawn_drones()

        self.current_turn = 0
        self.playing = False
