import sys
import os
from raylib.colors import RAYWHITE
from pyray import (
    begin_drawing, clear_background, close_window, end_drawing,
    gui_set_style, init_window, is_texture_valid, load_texture, set_target_fps,
    set_trace_log_level, unload_texture, window_should_close
    )
from raylib import DEFAULT, LOG_NONE, TEXT_SIZE
from src import Map, MapLayout, ParsingError, MapRenderer, Solver


DRONE_TEXTURE_PATH = "./images/drone-s.png"


def launch_visualizer(
        win_w: int,
        win_h: int,
        map_layout: MapLayout,
        turns: list[list[tuple[int, str]]]
        ) -> None:
    init_window(win_w, win_h, "Fly-in")
    gui_set_style(DEFAULT, TEXT_SIZE, 20)

    drone_texture = load_texture(DRONE_TEXTURE_PATH)
    renderer = MapRenderer(map_layout, drone_texture)
    renderer.load_turns(turns)

    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(RAYWHITE)

        renderer.handle_click()
        renderer.draw_map()
        renderer.draw_panel()

        end_drawing()

    unload_texture(drone_texture)
    close_window()


def build_layout(m: Map, tex_width: int) -> tuple[MapLayout, int, int]:
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
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]
    if not os.path.isfile(file):
        print(f"Error: map file not found '{file}'")
        sys.exit(1)

    m = Map()
    try:
        m.parse_file(file)
    except ParsingError as e:
        print(e)
        sys.exit(1)

    set_trace_log_level(LOG_NONE)

    if not os.path.isfile(DRONE_TEXTURE_PATH):
        print(f"Error: drone texture not found '{DRONE_TEXTURE_PATH}'")
        sys.exit(1)

    init_window(1, 1, "loading")
    texture = load_texture(DRONE_TEXTURE_PATH)

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
        launch_visualizer(win_w, win_h, map_layout, s.turns)
    except Exception as e:
        print(f"Visualiser Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
