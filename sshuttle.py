# -*- coding: utf-8 -*-
"""
Start/stop sshuttle and show status.

@author rixx
"""
import subprocess
import time


class Py3status:

    # available configuration parameters
    cache_timeout = 10
    hide_if_disconnected = False
    host = 'cutebit'
    ip = '88.198.169.75'
    pidfile = '/tmp/sshuttle'
    text_up = 'up'
    text_down = 'down'

    def __init__(self):
        self.last_check = 0
        self.status = 'unconnected'

    def check_sshuttle(self, i3s_output_list, i3s_config):
        response = {}

        if time.time() < self.last_check + self.cache_timeout:
            response['cached_until'] = self.last_check
        else:
            self.last_check = time.time()
            response['cached_until'] = self.last_check + self.cache_timeout

            if self._get_ip() == self.ip:
                self.status = 'connected'
            else:
                self.status = 'unconnected'

        if self.status == 'unconnected':
            response['full_text'] = self.text_down
            response['color'] = i3s_config['color_bad']
        elif self.status == 'connected':
            response['full_text'] = self.text_up
            response['color'] = i3s_config['color_good']
        return response

    def _get_ip(self):
        return subprocess.check_output(['curl','http://canihazip.com/s']).decode()

    def _is_running(self):
        return False

    def on_click(self, i3s_output_list, i3s_config, event):
        if self.status == 'connected':
            try:
                pid = open(self.pidfile).read().strip()
                subprocess.call(['kill', pid])
                self.status = 'unconnected'
            except:
                self.status = 'unconnected'
        else:
            p = '--pidfile=' + self.pidfile
            #subprocess.call(['/usr/local/bin/sshu'])
            #subprocess.call(['sshuttle', p, '--daemon', '--dns', '-r', self.host, '0/0'])
            self.status = 'connected'
        return None


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.check_sshuttle([], config))
        sleep(1)
        print(x.on_click(None, config, {}))
