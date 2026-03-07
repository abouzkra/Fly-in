import sys
from pyray import *
from raylib import LOG_NONE, TEXT_SIZE
from models import Map, MapLayout, ParsingError, MapRenderer
from models.solver import Solver

def launch_visualizer(
        win_w: int,
        win_h: int,
        map_layout: MapLayout,
        turns
        ) -> None:
    init_window(win_w, win_h, "Fly-in")
    gui_set_style(DEFAULT, TEXT_SIZE, 20)

    drone_texture = load_texture("./images/drone-s.png")
    renderer = MapRenderer(map_layout, drone_texture)
    renderer.load_turns(turns)

    set_target_fps(60)
    while not window_should_close():
        begin_drawing()

        renderer.handle_click()
        renderer.draw_map()
        renderer.draw_panel()

        clear_background(RAYWHITE)
        end_drawing()

    unload_texture(drone_texture)
    close_window()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]

    m = None
    try:
        m = Map()
        m.parse_file(file)
    except ParsingError as e:
        print(e)
        sys.exit(1)

    set_trace_log_level(LOG_NONE)
    init_window(200, 200, "loading")

    drone_texture = load_texture("./images/drone-s.png")
    map_layout = MapLayout(m, drone_texture.width)
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

    if win_w > get_monitor_width(0) or win_h > get_monitor_height(0):
        print("Warning: Map is too big for window!")
        print("Simulation output will be provided")
    # else:
        # try:
    s = Solver(m)
    s.solve()
    close_window()
    launch_visualizer(win_w, win_h, map_layout, s.turns) 
        # except Exception as e:
        #     print(f"Visualiser Error: {e}")
        #     sys.exit(1)


if __name__ == "__main__":
    main()
