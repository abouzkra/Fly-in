from pyray import *
from raylib import LOG_NONE, GetMousePosition, SetTargetFPS, SetTraceLogLevel


SetTraceLogLevel(LOG_NONE)

init_window(800, 450, "Hello")
drone_texture = load_texture_from_image(load_image("./images/camera-drone-med.png"))
drone_x = 400

SetTargetFPS(60)

while not window_should_close():

    if drone_x < 600:
        drone_x += 1
    else:
        drone_x = 400

    begin_drawing()

    draw_texture(drone_texture, drone_x, 200, BLACK)

    clear_background(RAYWHITE)
    draw_text("Hello world", 190, 200, 20, VIOLET)
    draw_circle_lines(100, 100, 30, MAGENTA)
    end_drawing()

unload_texture(drone_texture)
close_window()
