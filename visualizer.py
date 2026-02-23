from math import sqrt, ceil
from pyray import *
from raylib import LOG_NONE, SetTargetFPS, SetTraceLogLevel


# Zone drawing
if __name__ == "__main__":
    SetTraceLogLevel(LOG_NONE)

    init_window(800, 450, "Hello")
    drone_texture = load_texture("./images/drone-small.png")

    SetTargetFPS(60)
    while not window_should_close():

        begin_drawing()

        clear_background(RAYWHITE)
        end_drawing()

    unload_texture(drone_texture)
    close_window()


# Drone drawing
# if __name__ == "__main__":
#     SetTraceLogLevel(LOG_NONE)
#
#     init_window(800, 450, "Hello")
#     max_drones = 8
#     drone_texture = load_texture("./images/drone-small.png")
#
#     cols = rows = ceil(sqrt(max_drones))
#
#     padding = 8
#     grid_x, grid_y = 100, 100
#     grid_w = (drone_texture.width + padding) * cols - padding
#     grid_h = (drone_texture.height + padding) * rows - padding
#
#     SetTargetFPS(60)
#     while not window_should_close():
#
#         begin_drawing()
#         draw_circle(
#             (grid_x + grid_w // 2),
#             (grid_y + grid_h // 2),
#             sqrt((grid_w ** 2 + grid_h ** 2)) // 2 + padding,
#             LIGHTGRAY
#             )
#
#         # draw_rectangle_lines(grid_x, grid_y, grid_w, grid_h, BLUE)
#
#         count = 0
#         for row in range(rows):
#             for col in range(cols):
#                 if count >= max_drones:
#                     break
#                 draw_texture(
#                     drone_texture,
#                     grid_x + col * (drone_texture.width + padding),
#                     grid_y + row * (drone_texture.height + padding),
#                     WHITE
#                     )
#                 count += 1
#
#         clear_background(RAYWHITE)
#         end_drawing()
#
#     unload_texture(drone_texture)

