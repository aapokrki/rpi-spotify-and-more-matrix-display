from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from dateutil import tz


class ClockDisplay:
    def __init__(self):
        self.canvas_width = 64
        self.canvas_height = 64
        self.font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.text_color = (255, 255, 255)

    def generate(self):
        frame = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        draw = ImageDraw.Draw(frame)

        current_time = datetime.now(tz=tz.tzlocal())
        time_string = current_time.strftime("%I:%M")
        # date_string = current_time.strftime("%a, %b %d")

        # Center the text
        # wT, hT = draw.textsize(time_string, font=self.font)
        wT, hT = 32, 32
        # wD, hD = draw.textsize(date_string, font=self.font)

        draw.text(((self.canvas_width - wT) / 2, 20), time_string, self.text_color, font=self.font)
        # draw.text(((self.canvas_width - wD) / 2, 30), date_string, (161, 255, 220), font=self.font)

        return frame
