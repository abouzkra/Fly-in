import sys
from pyray import *
from raylib import LOG_NONE, GetMonitorHeight, GetMonitorWidth, SetTargetFPS, SetTraceLogLevel
from models import Map, MapLayout, ParsingError
from models.renderer import MapRenderer
from models.solver import Solver


def launch_visualizer(
        win_w: int,
        win_h: int,
        map_layout: MapLayout
        ) -> None:
    close_window()
    init_window(win_w, win_h, "Fly-in")

    drone_texture = load_texture("./images/drone-s.png")
    renderer = MapRenderer(map_layout, drone_texture)

    SetTargetFPS(60)
    while not window_should_close():
        begin_drawing()

        renderer.draw()

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

        s = Solver(m)
        turns = s.solve()
        print(len(turns))

        # for i, mv in enumerate(turns, start=1):
        #     print(f"{i}: {mv}")
    except ParsingError as e:
        print(e)
        sys.exit(1)

    SetTraceLogLevel(LOG_NONE)
    init_window(200, 200, "loading")

    drone_texture = load_texture("./images/drone-s.png")
    map_layout = MapLayout(m, drone_texture.width)
    win_w = int(max(
        layout.container.x + layout.container.w
        for layout in map_layout.zone_layouts.values()
        ))
    win_h = int(max(
        layout.container.y + layout.container.h
        for layout in map_layout.zone_layouts.values()
        ))


    if win_w > GetMonitorWidth(0) or win_h > GetMonitorHeight(0):
        print("Warning: Map is too big for window!")
        print("Simulation output will be provided")
    else:
        # try:
        launch_visualizer(win_w, win_h, map_layout)
        # except Exception as e:
        #     print(f"Visualiser Error: {e}")
        #     sys.exit(1)


if __name__ == "__main__":
    main()
