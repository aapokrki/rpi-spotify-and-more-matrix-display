import os, inspect, sys, math, time, configparser, argparse, warnings, keyboard
from PIL import Image, ImageFont, ImageDraw

from apps_v2 import spotify_player
from modules import spotify_module

from apps_v2 import test_display
from modules import test_module
def main():
    canvas_width = 64
    canvas_height = 64

    # get arguments
    parser = argparse.ArgumentParser(
                    prog = 'RpiSpotifyMatrixDisplay',
                    description = 'Displays album art of currently playing song on an LED matrix')

    parser.add_argument('-f', '--fullscreen', action='store_true', help='Always display album art in fullscreen')
    parser.add_argument('-e', '--emulated', action='store_true', help='Run in a matrix emulator')
    args = parser.parse_args()

    is_emulated = args.emulated
    is_full_screen_always = args.fullscreen

    # switch matrix library import if emulated
    if is_emulated:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    else:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

    # get config
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(currentdir+"/rpi-rgb-led-matrix/bindings/python")

    config = configparser.ConfigParser()
    parsed_configs = config.read('../config.ini')

    if len(parsed_configs) == 0:
        print("no config file found")
        sys.exit()

    # connect to Spotify and create display image
    modules = { 'spotify' : spotify_module.SpotifyModule(config), 'test' : test_module.TestModule(config) }
    app_list = [ spotify_player.SpotifyScreen(config, modules, is_full_screen_always), test_display.ClockDisplay()]

    # setup matrix
    options = RGBMatrixOptions()
    options.hardware_mapping = config.get('Matrix', 'hardware_mapping', fallback='regular')
    options.rows = canvas_width
    options.cols = canvas_height
    options.brightness = 100 if is_emulated else config.getint('Matrix', 'brightness', fallback=100)
    options.gpio_slowdown = config.getint('Matrix', 'gpio_slowdown', fallback=1)
    options.limit_refresh_rate_hz = config.getint('Matrix', 'limit_refresh_rate_hz', fallback=0)
    options.drop_privileges = False
    matrix = RGBMatrix(options = options)

    shutdown_delay = config.getint('Matrix', 'shutdown_delay', fallback=600)
    black_screen = Image.new("RGB", (canvas_width, canvas_height), (0,0,0))
    last_active_time = math.floor(time.time())

    no_spotify_screen = Image.new("RGB", (canvas_width, canvas_height), (0,0,0))
    draw = ImageDraw.Draw(no_spotify_screen)
    draw.text((11, 24), "Spotify Not", (255, 255, 255), ImageFont.truetype("fonts/tiny.otf", 5))
    draw.text((19, 36), "Running", (255, 255, 255), ImageFont.truetype("fonts/tiny.otf", 5))

    def pressSpace():
        frame = app_list[1].generate()
        while(frame is not None):
            matrix.SetImage(frame)
            time.sleep(0.08)
            frame = app_list[1].generate()

            #add other screens here
            if keyboard.is_pressed('alt'):
                return pressS()
        return frame

    def pressS():
        last_active_time = math.floor(time.time())
        current_time = math.floor(time.time())
        frame, is_playing = app_list[0].generate()
        count = 0
        while (frame is None and count < 20):
            frame, is_playing = app_list[0].generate()
            count += 1
            # print('no spotify')
        while (frame is not None):
            # print('got spotify')
            frame, is_playing = app_list[0].generate()
            if frame is not None:
                if is_playing:
                    last_active_time = math.floor(time.time())
                elif current_time - last_active_time >= shutdown_delay:
                    frame = black_screen
            else:
                frame = no_spotify_screen
                is_playing = False

            # add other screens here
            if keyboard.is_pressed('space'):
                return pressSpace()

            matrix.SetImage(frame)
            time.sleep(0.08)

        # if frame != None:
        #     matrix.SetImage(frame)
        #     time.sleep(0.08)
        #     return frame
        return no_spotify_screen

    gloframe = None

    # generate image
    while(True):

        if(gloframe is None):
            print('gloframe is none')
            gloframe = black_screen

        if(gloframe is not None):
            if(keyboard.is_pressed('space')):
                switchedTime = math.floor(time.time())
                gloframe = pressSpace()
            elif(keyboard.is_pressed('alt')):
                switchedTime = math.floor(time.time())
                gloframe = pressS()

            firstTime = math.floor(time.time())
            matrix.SetImage(gloframe)
            time.sleep(0.08)

if __name__ == '__main__':
    try:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        main()
    except KeyboardInterrupt:
        print('Interrupted with Ctrl-C')
        sys.exit(0)
