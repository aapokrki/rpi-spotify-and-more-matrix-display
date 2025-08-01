import numpy as np, requests, math, time, threading
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

class SpotifyScreen:
    def __init__(self, config, modules, fullscreen):
        self.modules = modules

        self.font = ImageFont.truetype("fonts/tiny.otf", 5)

        self.canvas_width = 64
        self.canvas_height = 64
        self.title_color = (255,255,255)
        self.artist_color = (255,255,255)
        self.play_color = (102, 240, 110)

        self.full_screen_always = fullscreen

        self.current_art_url = ''
        self.current_art_img = None
        self.current_title = ''
        self.current_artist = ''

        self.title_animation_cnt = 0
        self.artist_animation_cnt = 0
        self.last_title_reset = math.floor(time.time())
        self.last_artist_reset = math.floor(time.time())
        self.scroll_delay = 4

        self.paused = True
        self.paused_time = math.floor(time.time())
        self.paused_delay = 5

        self.is_playing = False

        self.last_fetch_time = math.floor(time.time())
        self.fetch_interval = 1
        self.spotify_module = self.modules['spotify']

        self.response = None
        self.thread = threading.Thread(target=self.getCurrentPlaybackAsync)
        self.thread.start()

    def getCurrentPlaybackAsync(self):
        # delay spotify fetches
        time.sleep(3)
        while True:
            self.response = self.spotify_module.getCurrentPlayback()
            time.sleep(1)

    def generate(self):
        if not self.spotify_module.queue.empty():
            self.response = self.spotify_module.queue.get()
            self.spotify_module.queue.queue.clear()
        return self.generateFrame(self.response)

    def generateFrame(self, response):
        if response is not None:
            (artist, title, art_url, self.is_playing, progress_ms, duration_ms) = response

            if self.full_screen_always:
                if self.current_art_url != art_url:
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    self.current_art_img = img.resize((self.canvas_width, self.canvas_height), resample=Image.LANCZOS)

                frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
                draw = ImageDraw.Draw(frame)

                frame.paste(self.current_art_img, (0,0))
                return (frame, self.is_playing)
            else:
                if not self.is_playing:
                    if not self.paused:
                        self.paused_time = math.floor(time.time())
                        self.paused = True
                else:
                    if self.paused and self.current_art_img and self.current_art_img.size == (self.canvas_width, self.canvas_height):
                        self.title_animation_cnt = 0
                        self.artist_animation_cnt = 0
                        self.last_title_reset = math.floor(time.time())
                        self.last_artist_reset = math.floor(time.time())
                    self.paused_time = math.floor(time.time())
                    self.paused = False

                if (self.current_title != title or self.current_artist != artist):
                    self.current_artist = artist
                    self.current_title = title
                    self.title_animation_cnt = 0
                    self.artist_animation_cnt = 0
                    self.last_title_reset = math.floor(time.time())
                    self.last_artist_reset = math.floor(time.time())

                current_time = math.floor(time.time())
                show_fullscreen = current_time - self.paused_time >= self.paused_delay

                # show fullscreen album art after pause delay
                if show_fullscreen and self.current_art_img.size == (48, 48):
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    self.current_art_img = img.resize((self.canvas_width, self.canvas_height), resample=Image.LANCZOS)
                elif not show_fullscreen and (self.current_art_url != art_url or self.current_art_img.size == (self.canvas_width, self.canvas_height)):
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    self.current_art_img = img.resize((48, 48), resample=Image.LANCZOS)

                frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
                draw = ImageDraw.Draw(frame)

                # exit early if fullscreen
                if self.current_art_img is not None:
                    if show_fullscreen:
                        frame.paste(self.current_art_img, (0,0))
                        return (frame, self.is_playing)
                    else:
                        frame.paste(self.current_art_img, (8,14))

                freeze_title = self.title_animation_cnt == 0 and self.artist_animation_cnt > 0
                freeze_artist = self.artist_animation_cnt == 0 and self.title_animation_cnt > 0

                title_len = self.font.getlength(self.current_title)
                artist_len = self.font.getlength(self.current_artist)

                text_length = self.canvas_width - 12
                x_offset = 1
                spacer = "     "

                if title_len > text_length:
                    draw.text((x_offset-self.title_animation_cnt, 1), self.current_title + spacer + self.current_title, self.title_color, font = self.font)
                    if current_time - self.last_title_reset >= self.scroll_delay:
                        self.title_animation_cnt += 1
                    if freeze_title or self.title_animation_cnt == self.font.getlength(self.current_title + spacer):
                        self.title_animation_cnt = 0
                        self.last_title_reset = math.floor(time.time())
                else:
                    draw.text((x_offset-self.title_animation_cnt, 1), self.current_title, self.title_color, font = self.font)

                if artist_len > text_length:
                    draw.text((x_offset-self.artist_animation_cnt, 7), self.current_artist + spacer + self.current_artist, self.artist_color, font = self.font)
                    if current_time - self.last_artist_reset >= self.scroll_delay:
                        self.artist_animation_cnt += 1
                    if freeze_artist or self.artist_animation_cnt == self.font.getlength(self.current_artist + spacer):
                        self.artist_animation_cnt = 0
                        self.last_artist_reset = math.floor(time.time())
                else:
                    draw.text((x_offset-self.artist_animation_cnt, 7), self.current_artist, self.artist_color, font = self.font)

                draw.rectangle((0,0,0,12), fill=(0,0,0))
                draw.rectangle((52,0,63,12), fill=(0,0,0))

                line_y = 63
                draw.rectangle((0,line_y-1,63,line_y), fill=(100,100,100))
                draw.rectangle((0,line_y-1,0+round(((progress_ms / duration_ms) * 100) // 1.57), line_y), fill=self.play_color)
                drawPlayPause(draw, self.is_playing, self.play_color)
                
                return (frame, self.is_playing)
        else:
            #not active
            frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0,0,0))
            draw = ImageDraw.Draw(frame)

            self.current_art_url = ''
            self.is_playing = False
            self.title_animation_cnt = 0
            self.artist_animation_cnt = 0
            self.last_title_reset = math.floor(time.time())
            self.last_artist_reset = math.floor(time.time())
            self.paused = True
            self.paused_time = math.floor(time.time())

            return (None, self.is_playing)

def drawPlayPause(draw, is_playing, color):
    x = 10
    y = -16
    if not is_playing:
        draw.line((x+45,y+19,x+45,y+25), fill = color)
        draw.line((x+46,y+20,x+46,y+24), fill = color)
        draw.line((x+47,y+20,x+47,y+24), fill = color)
        draw.line((x+48,y+21,x+48,y+23), fill = color)
        draw.line((x+49,y+21,x+49,y+23), fill = color)
        draw.line((x+50,y+22,x+50,y+22), fill = color)
    else:
        draw.line((x+45,y+19,x+45,y+25), fill = color)
        draw.line((x+46,y+19,x+46,y+25), fill = color)
        draw.line((x+49,y+19,x+49,y+25), fill = color)
        draw.line((x+50,y+19,x+50,y+25), fill = color)
