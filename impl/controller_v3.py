import os, sys, math, time, configparser, argparse, warnings, inspect
from PIL import Image, ImageDraw, ImageFont
from threading import Thread
import signal

from frames import spotify_player, clock
from modules import spotify_module, test_module

from app import run_flask, get_selected_mode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--fullscreen', action='store_true')
    parser.add_argument('-e', '--emulated', action='store_true')
    args = parser.parse_args()

    is_emulated = args.emulated
    is_full_screen_always = args.fullscreen

    if is_emulated:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    else:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '../config.ini')
    if not config.read(config_path):
        print("No config file found")
        sys.exit(1)

    # Matrix setup
    canvas_width = 64
    canvas_height = 64

    options = RGBMatrixOptions()
    options.hardware_mapping = config.get('Matrix', 'hardware_mapping', fallback='regular')
    options.rows = canvas_width
    options.cols = canvas_height
    options.brightness = 100 if is_emulated else config.getint('Matrix', 'brightness', fallback=100)
    options.gpio_slowdown = config.getint('Matrix', 'gpio_slowdown', fallback=1)
    options.limit_refresh_rate_hz = config.getint('Matrix', 'limit_refresh_rate_hz', fallback=0)
    options.drop_privileges = False

    matrix = RGBMatrix(options=options)

    # App setup
    modules = {
        'spotify': spotify_module.SpotifyModule(config),
        'test': test_module.TestModule(config)
    }
    app_list = [
        spotify_player.SpotifyScreen(config, modules, is_full_screen_always),
        clock.ClockDisplay()
    ]

    shutdown_delay = config.getint('Matrix', 'shutdown_delay', fallback=600)
    last_active_time = math.floor(time.time())

    black_screen = Image.new("RGB", (canvas_width, canvas_height), (0, 0, 0))
    no_spotify_screen = Image.new("RGB", (canvas_width, canvas_height), (0, 0, 0))
    draw = ImageDraw.Draw(no_spotify_screen)
    draw.text((11, 24), "Spotify Not", (255, 255, 255), ImageFont.truetype("fonts/tiny.otf", 5))
    draw.text((19, 36), "Running", (255, 255, 255), ImageFont.truetype("fonts/tiny.otf", 5))

    def show_clock():
        frame = app_list[1].generate()
        while frame and get_selected_mode() == "clock":
            matrix.SetImage(frame)
            time.sleep(0.08)
            frame = app_list[1].generate()

    def show_spotify():
        nonlocal last_active_time
        count = 0
        frame, is_playing = app_list[0].generate()

        while frame is None and count < 20:
            frame, is_playing = app_list[0].generate()
            count += 1

        while frame and get_selected_mode() == "spotify":
            frame, is_playing = app_list[0].generate()
            if frame:
                if is_playing:
                    last_active_time = math.floor(time.time())
                elif time.time() - last_active_time > shutdown_delay:
                    frame = black_screen
            else:
                frame = no_spotify_screen
            matrix.SetImage(frame)
            time.sleep(0.08)

    def signal_handler(sig, frame):
        print("Exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start web server
    Thread(target=run_flask, daemon=True).start()

    while True:
        mode = get_selected_mode()
        print(mode)
        if mode == "clock":
            show_clock()
        elif mode == "spotify":
            show_spotify()
        else:
            matrix.SetImage(black_screen)
            time.sleep(0.1)

if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()



