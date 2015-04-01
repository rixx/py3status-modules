# -*- coding: utf-8 -*-
"""
Volume control

@author rixx, inspired by player_control in py3status
"""

import time
import subprocess


class Py3status:

    mute_text = 'mute'
    volume_text = 'volume: {volume}'
    volume_tick = 1

    def __init__(self):
        self.volume = self._get_volume()
        self.mute = self._is_mute()

    def on_click(self, i3s_output_list, i3s_config, event):
        buttons = (None, 'left', 'middle', 'right', 'up', 'down')
        try:
            button = buttons[event['button']]
        except IndexError:
            return

        if button in ('up', 'down'):
            self._change_volume(button == 'up')
        else:
            self._toggle_mute()

    def _change_volume(self, increase):
        """Change volume using amixer
        """
        sign = '%+' if increase else '%-'
        delta = str(self.volume_tick) + sign
        subprocess.call(['amixer', '-q', 'sset', 'Master', delta])

    def _get_volume(self):
        out = subprocess.check_output(['amixer', 'sget', 'Master']).decode()
        a = out.find('[')
        b = out.find(']')
        return int(out[a+1:b-1])

    def _is_mute(self):
        out = subprocess.check_output(['amixer', 'sget', 'Master']).decode()
        if '[on]' in out:
            return False
        return True

    def _toggle_mute(self):
        if self._is_mute():
            attr = 'unmute'
        else:
            attr = 'mute'
        subprocess.call(['amixer', '-q', 'sset', 'Master', attr])

    def volume_control(self, i3s_output_list, i3s_config):
        response = {'cached_until': time.time()}
        self.volume = self._get_volume()
        self.mute = self._is_mute()

        if self.mute:
            response['color'] = i3s_config['color_bad']
            response['full_text'] = self.mute_text.format(volume=self.volume)
        else:
            response['color'] = i3s_config['color_good']
            response['full_text'] = self.volume_text.format(volume=self.volume)

        return response


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.volume_control([], config))
        time.sleep(1)
