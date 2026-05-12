import sys
import os
from raylib.colors import LIGHTGRAY
from pyray import (
    Texture, begin_drawing, clear_background, end_drawing, get_monitor_height,
    get_monitor_width, gui_set_style, init_window, is_texture_valid,
    load_texture, set_target_fps, set_trace_log_level, unload_texture,
    window_should_close, close_window
    )
from raylib import DEFAULT, LOG_NONE, TEXT_SIZE
from Map import Map
from error import ParsingError
from renderer import MapRenderer
from layout import MapLayout
from solver import Solver


DRONE_TEXTURE_PATH = "./images/drone.png"


def print_output(solver: Solver) -> None:
    """Provides simulation output in case of a program failure.

    Args:
        solver (Solver): The solver instance which contains turns.
    """
    for i in range(len(solver.turns)):
        print(solver.format_turn(i))


def launch_visualizer(
        win_w: int,
        win_h: int,
        map_layout: MapLayout,
        solver: Solver
        ) -> None:
    """Launches the visualiser.

    Args:
        win_w (int): Window width.
        win_h (int): Window height.
        map_layout (MapLayout): Precomputed layout of the map and panel.
        solver (Solver): The solver instance which contains turns.
    """
    init_window(win_w, win_h, "Fly-in")
    if win_w > get_monitor_width(0) or win_h > get_monitor_height(0):
        close_window()
        print("Visualiser Error: window dimensions are too big for screen")
        print("============== Providing simulation output ==============")
        print_output(solver)
        sys.exit(0)

    gui_set_style(DEFAULT, TEXT_SIZE, 20)

    drone_texture = load_texture(DRONE_TEXTURE_PATH)
    renderer = MapRenderer(map_layout, drone_texture, solver)

    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(LIGHTGRAY)

        renderer.handle_click()
        renderer.draw_map()
        renderer.draw_panel()

        end_drawing()

    unload_texture(drone_texture)
    close_window()


def build_layout(m: Map, tex_width: int) -> tuple[MapLayout, int, int]:
    """Builds the layout of the map and panel.

    Args:
        m (Map): The map to build the layout for.
        tex_width (int): The width of the drone texture.

    Returns:
        tuple[MapLayout, int, int]: The built layout and window dimensions.
    """
    map_layout = MapLayout(m, tex_width)

    win_w = max(
        int(max(
            layout.container.x + layout.container.width
            for layout in map_layout.zone_layouts.values()
        )),
        int(map_layout.panel_layout.container.width)
    )
    win_h = int(max(
        layout.container.y + layout.container.height
        for layout in map_layout.zone_layouts.values()
        )) + int(map_layout.panel_layout.container.height)

    return map_layout, win_w, win_h


def main() -> None:
    """Main function to run the program."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]

    try:
        m = Map()
        m.parse_file(file)
    except (
            FileNotFoundError, PermissionError, IsADirectoryError,
            ParsingError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    set_trace_log_level(LOG_NONE)

    if not os.path.isfile(DRONE_TEXTURE_PATH):
        print(f"Error: drone texture not found '{DRONE_TEXTURE_PATH}'")
        sys.exit(1)

    init_window(1, 1, "loading")

    texture: Texture = load_texture(DRONE_TEXTURE_PATH)
    if not is_texture_valid(texture):
        close_window()
        print(f"Error: failed to load drone texture '{DRONE_TEXTURE_PATH}'")
        sys.exit(1)

    tex_width = texture.width
    unload_texture(texture)
    close_window()

    try:
        s = Solver(m)
        s.solve()
    except Exception as e:
        print(f"Solver Error: {e}")
        sys.exit(1)

    map_layout, win_w, win_h = build_layout(m, tex_width)

    try:
        launch_visualizer(win_w, win_h, map_layout, s)
    except Exception as e:
        print(f"Visualiser Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
