# -*- coding: utf-8 -*-
"""
Backlight control

@author rixx
"""

import time
import subprocess


class Py3status:

    text = 'brightness: {brightness}'
    tick = 5

    def __init__(self):
        self.volume = self._get_brightness()

    def volume_control(self, i3s_output_list, i3s_config):
        response = {'cached_until': time.time()}
        self.brightness = self._get_brightness()

        response['full_text'] = self.text.format(brightness=self.brightness)
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        buttons = (None, 'left', 'middle', 'right', 'up', 'down')
        try:
            button = buttons[event['button']]
        except IndexError:
            return

        if button in ('up', 'down'):
            self._change_brightness(button == 'up')

    def _change_brightness(self, increase):
        direction = '-inc' if increase else '-dec'
        subprocess.check_output(['xbacklight', direction, str(self.tick)])

    def _get_brightness(self):
        out = subprocess.check_output(['xbacklight', '-get']).decode()
        return round(float(out))


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.volume_control([], config))
        time.sleep(1)
        print(x.on_click([], config, {'button':4}))
